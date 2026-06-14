"""
SSG.COM 특가 데이터 EDA(탐색적 데이터 분석) 및 시각화 스크립트

이 스크립트는 수집된 여러 시점의 해피바이 특가 CSV 데이터를 로드하여 병합하고,
기본 정보 확인, 기술 통계량 산출, 일변량/이변량/다변량 변수 분석 및 시각화를 수행합니다.
시각화 결과 이미지(10개 이상)는 ssg_com/images/ 폴더에 저장되며,
분석 리포트 작성을 위한 각종 통계 수치가 콘솔 및 마크다운 형식으로 출력됩니다.
"""
# -*- coding: utf-8 -*-
import os
import glob
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
import koreanize_matplotlib
from git_hook import execute_git_commit

# 경로 설정
DATA_DIR = "ssg_com/data"
IMAGE_DIR = "ssg_com/images"
REPORT_DIR = "ssg_com/reports"

# 출력 폴더 생성
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

def load_and_merge_data():
    """
    data 디렉터리 내의 모든 happybuy CSV 파일을 찾아 병합하고 정제합니다.
    """
    csv_files = glob.glob(os.path.join(DATA_DIR, "happybuy_*.csv"))
    if not csv_files:
        raise FileNotFoundError("분석할 CSV 파일이 ssg_com/data/ 폴더에 존재하지 않습니다.")
    
    print(f"발견된 CSV 파일 수: {len(csv_files)}")
    df_list = []
    for f in csv_files:
        # utf-8-sig 인코딩으로 로드
        tmp = pd.read_csv(f, encoding="utf-8-sig")
        df_list.append(tmp)
        
    df = pd.concat(df_list, ignore_index=True)
    
    # 데이터 정제 및 수치화
    # 할인율을 수치화 (예: '58%' -> 58.0)
    df["할인율_수치"] = df["할인율"].str.replace("%", "", regex=False).astype(float)
    
    # 정상가와 판매가를 정수형으로 확실히 변환
    df["정상가"] = pd.to_numeric(df["정상가"], errors="coerce")
    df["판매가"] = pd.to_numeric(df["판매가"], errors="coerce")
    
    # 결측치 채우기 (정상가가 비어있으면 판매가로 대체)
    df["정상가"] = df["정상가"].fillna(df["판매가"])
    df["할인율_수치"] = df["할인율_수치"].fillna(0.0)
    
    # 수집일시를 datetime 형태로 파싱하여 새 컬럼 추가
    df["수집일시_dt"] = pd.to_datetime(df["수집일시"])
    
    return df

def generate_visualizations(df):
    """
    데이터프레임을 바탕으로 10개 이상의 개별 그래프를 시각화하여 images/ 폴더에 저장하고,
    리포트에 삽입할 통계표 데이터를 생성하여 출력합니다.
    """
    stats_tables = {}
    
    # ----------------------------------------------------
    # 1. 판매가 분포 히스토그램 (일변량)
    # ----------------------------------------------------
    plt.figure(figsize=(8, 5))
    plt.hist(df["판매가"], bins=20, color="royalblue", edgecolor="black", alpha=0.7)
    plt.title("특가 상품 판매가 분포")
    plt.xlabel("판매가 (원)")
    plt.ylabel("빈도수 (개)")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, "01_sales_price_distribution.png"))
    plt.close()
    
    # 통계표 1: 판매가 사분위 및 요약
    stats_tables["01_sales_price"] = df["판매가"].describe().to_frame().to_markdown()

    # ----------------------------------------------------
    # 2. 정상가 분포 히스토그램 (일변량)
    # ----------------------------------------------------
    plt.figure(figsize=(8, 5))
    plt.hist(df["정상가"], bins=20, color="salmon", edgecolor="black", alpha=0.7)
    plt.title("특가 상품 정상가 분포")
    plt.xlabel("정상가 (원)")
    plt.ylabel("빈도수 (개)")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, "02_normal_price_distribution.png"))
    plt.close()
    
    # 통계표 2: 정상가 요약
    stats_tables["02_normal_price"] = df["정상가"].describe().to_frame().to_markdown()

    # ----------------------------------------------------
    # 3. 할인율 수치 분포 (일변량)
    # ----------------------------------------------------
    plt.figure(figsize=(8, 5))
    plt.hist(df["할인율_수치"], bins=15, color="mediumseagreen", edgecolor="black", alpha=0.7)
    plt.title("특가 상품 할인율 분포")
    plt.xlabel("할인율 (%)")
    plt.ylabel("빈도수 (개)")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, "03_discount_rate_distribution.png"))
    plt.close()
    
    # 통계표 3: 할인율 요약
    stats_tables["03_discount_rate"] = df["할인율_수치"].describe().to_frame().to_markdown()

    # ----------------------------------------------------
    # 4. 수집 시점별 상품 개수 분포 (일변량/시간별)
    # ----------------------------------------------------
    time_counts = df["수집일시"].value_counts().sort_index()
    plt.figure(figsize=(9, 5))
    time_counts.plot(kind="bar", color="skyblue", edgecolor="black", alpha=0.8)
    plt.title("수집 시점별 수집 완료 상품 수")
    plt.xlabel("수집 일시")
    plt.ylabel("상품 수 (개)")
    plt.xticks(rotation=15)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, "04_time_collect_counts.png"))
    plt.close()
    
    # 통계표 4: 수집 시점별 카운트
    stats_tables["04_time_counts"] = time_counts.to_frame(name="상품수").to_markdown()

    # ----------------------------------------------------
    # 5. 정상가 vs 판매가 상관 산점도 (이변량)
    # ----------------------------------------------------
    plt.figure(figsize=(8, 6))
    plt.scatter(df["정상가"], df["판매가"], color="purple", alpha=0.5, edgecolors="white")
    # 대각선 (할인이 전혀 없는 기준선)
    max_val = max(df["정상가"].max(), df["판매가"].max())
    plt.plot([0, max_val], [0, max_val], color="gray", linestyle="--", label="할인 없음 (정가=판매가)")
    plt.title("정상가 대비 판매가 산점도")
    plt.xlabel("정상가 (원)")
    plt.ylabel("판매가 (원)")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, "05_price_scatterplot.png"))
    plt.close()
    
    # 통계표 5: 피어슨 상관계수
    corr = df[["정상가", "판매가"]].corr()
    stats_tables["05_price_corr"] = corr.to_markdown()

    # ----------------------------------------------------
    # 6. 수집 시점별 평균 가격 추이 라인 차트 (이변량)
    # ----------------------------------------------------
    time_avg_price = df.groupby("수집일시")[["정상가", "판매가"]].mean().sort_index()
    plt.figure(figsize=(9, 5))
    plt.plot(time_avg_price.index, time_avg_price["정상가"], marker="o", color="tomato", label="평균 정상가")
    plt.plot(time_avg_price.index, time_avg_price["판매가"], marker="s", color="dodgerblue", label="평균 판매가")
    plt.title("수집 시점별 평균 가격(정상가/판매가) 추이")
    plt.xlabel("수집 일시")
    plt.ylabel("평균 가격 (원)")
    plt.xticks(rotation=15)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, "06_avg_price_trend.png"))
    plt.close()
    
    # 통계표 6: 시점별 평균가 테이블
    stats_tables["06_time_avg_price"] = time_avg_price.to_markdown()

    # ----------------------------------------------------
    # 7. 할인율 구간별 판매가 분포 Boxplot (이변량)
    # ----------------------------------------------------
    # 할인율을 구간별로 범주화 (예: 0~10%, 10~30%, 30~50%, 50% 이상)
    bins = [-1, 10, 30, 50, 101]
    labels = ["10% 이하", "10%~30%", "30%~50%", "50% 초과"]
    df["할인율_구간"] = pd.cut(df["할인율_수치"], bins=bins, labels=labels)
    
    plt.figure(figsize=(8, 6))
    sns.boxplot(x="할인율_구간", y="판매가", data=df, palette="Set2")
    plt.title("할인율 구간별 판매가 박스 플롯")
    plt.xlabel("할인율 구간")
    plt.ylabel("판매가 (원)")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, "07_discount_box_plot.png"))
    plt.close()
    
    # 통계표 7: 할인율 구간별 판매가 평균 및 개수
    discount_box_summary = df.groupby("할인율_구간")["판매가"].agg(["count", "mean", "std", "min", "max"])
    stats_tables["07_discount_box_summary"] = discount_box_summary.to_markdown()

    # ----------------------------------------------------
    # 8. 상품명 텍스트 TF-IDF 키워드 상위 30개 가로 막대 그래프 (텍스트 분석)
    # ----------------------------------------------------
    # 상품명 수집 컬럼
    corpus = df["상품명"].dropna().tolist()
    
    # 불용어 처리가 간단하도록 한글 단어 매칭
    vectorizer = TfidfVectorizer(max_features=100, stop_words=None, token_pattern=r'(?u)\b\w\w+\b')
    tfidf_matrix = vectorizer.fit_transform(corpus)
    feature_names = vectorizer.get_feature_names_out()
    
    # 단어별 TF-IDF 평균 가중치 계산
    mean_tfidf = np.asarray(tfidf_matrix.mean(axis=0)).ravel()
    tfidf_df = pd.DataFrame({"키워드": feature_names, "가중치": mean_tfidf})
    top_30_keywords = tfidf_df.sort_values(by="가중치", ascending=False).head(30)
    
    plt.figure(figsize=(10, 8))
    plt.barh(top_30_keywords["키워드"].iloc[::-1], top_30_keywords["가중치"].iloc[::-1], color="teal", alpha=0.8)
    plt.title("특가 상품명 핵심 키워드 중요도 Top 30 (TF-IDF)")
    plt.xlabel("평균 TF-IDF 가중치")
    plt.ylabel("단어")
    plt.grid(axis="x", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, "08_tfidf_keywords.png"))
    plt.close()
    
    # 통계표 8: TF-IDF 중요도 테이블
    stats_tables["08_tfidf_table"] = top_30_keywords.to_markdown(index=False)

    # ----------------------------------------------------
    # 9. 수집 시점별 평균 할인율 변화 추이 라인 차트 (이변량)
    # ----------------------------------------------------
    time_avg_discount = df.groupby("수집일시")["할인율_수치"].mean().sort_index()
    plt.figure(figsize=(9, 5))
    plt.plot(time_avg_discount.index, time_avg_discount.values, marker="d", color="darkcyan", linestyle="-.", linewidth=2)
    plt.title("수집 시점별 평균 할인율 변화 추이")
    plt.xlabel("수집 일시")
    plt.ylabel("평균 할인율 (%)")
    plt.xticks(rotation=15)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, "09_avg_discount_trend.png"))
    plt.close()
    
    # 통계표 9: 시점별 평균 할인율 테이블
    stats_tables["09_time_avg_discount"] = time_avg_discount.to_frame(name="평균할인율(%)").to_markdown()

    # ----------------------------------------------------
    # 10. 판매가와 정상가 간의 상관관계 히트맵 (다변량)
    # ----------------------------------------------------
    plt.figure(figsize=(7, 5))
    # 상관관계 행렬 계산
    corr_matrix = df[["정상가", "판매가", "할인율_수치"]].corr()
    sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", fmt=".3f", linewidths=.5, vmin=-1, vmax=1)
    plt.title("특가 상품 가격 변수 간 상관관계 히트맵")
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, "10_correlation_heatmap.png"))
    plt.close()
    
    # 통계표 10: 상관행렬 데이터
    stats_tables["10_corr_matrix"] = corr_matrix.to_markdown()

    # ----------------------------------------------------
    # 11. 정상가-판매가-할인율의 3D 버블 차트 또는 이변량 분포 결합 산점도 (다변량)
    # ----------------------------------------------------
    # 정상가와 판매가 산점도를 그리되, 할인율 크기를 점의 크기(size)와 색상(color)으로 매핑
    plt.figure(figsize=(9, 7))
    scatter = plt.scatter(
        df["정상가"], 
        df["판매가"], 
        c=df["할인율_수치"], 
        s=df["할인율_수치"] * 5 + 20, 
        cmap="viridis", 
        alpha=0.6, 
        edgecolors="none"
    )
    plt.title("정상가 vs 판매가 vs 할인율 (다변량 분석)")
    plt.xlabel("정상가 (원)")
    plt.ylabel("판매가 (원)")
    cbar = plt.colorbar(scatter)
    cbar.set_label("할인율 (%)")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, "11_multivariate_bubble.png"))
    plt.close()
    
    # 통계표 11: 주요 변수들의 다차원 평균 요약
    pivot_summary = df.pivot_table(
        index="할인율_구간", 
        values=["정상가", "판매가", "할인율_수치"], 
        aggfunc={"정상가": "mean", "판매가": "mean", "할인율_수치": "count"}
    ).rename(columns={"할인율_수치": "상품수"}).to_markdown()
    stats_tables["11_pivot_summary"] = pivot_summary
    
    return stats_tables

def main():
    print("데이터 분석 및 EDA 시각화를 시작합니다...")
    try:
        df = load_and_merge_data()
        
        # 기본 정보 출력
        print("\n" + "="*40)
        print("기본 데이터 정보")
        print("="*40)
        print(f"전체 크기: {df.shape[0]}행 x {df.shape[1]}열")
        print(f"중복 데이터 수: {df.duplicated().sum()}")
        print("\n[head 5행]")
        print(df.head(5).to_markdown())
        print("\n[tail 5행]")
        print(df.tail(5).to_markdown())
        print("\n[info 요약]")
        print(df.info())
        
        # 기술통계 정보
        print("\n" + "="*40)
        print("수치형 변수 기술통계")
        print("="*40)
        print(df[["정상가", "판매가", "할인율_수치"]].describe().to_markdown())
        
        print("\n" + "="*40)
        print("범주형 변수 기술통계")
        print("="*40)
        # 범주형으로 쓸만한 object 컬럼들
        print(df[["상품명", "할인율", "수집일시"]].describe(include=["object"]).to_markdown())
        
        # 시각화 및 마크다운 통계표 생성
        stats_tables = generate_visualizations(df)
        
        # 통계표 텍스트로 보존 (리포트 자동 생성용 백업)
        with open(os.path.join(REPORT_DIR, "raw_stats_tables.json"), "w", encoding="utf-8") as f:
            json.dump(stats_tables, f, ensure_ascii=False, indent=2)
            
        print("\n[성공] 모든 시각화 이미지(11개)가 ssg_com/images/ 폴더에 저장되었으며, 통계표가 생성되었습니다.")
        
        # Git Hook을 통한 자동 커밋 실행
        # 리포트 및 이미지 폴더를 자동 커밋
        report_file = os.path.join(REPORT_DIR, "EDA_Report.md")
        execute_git_commit([report_file, IMAGE_DIR], "[분석 리포트] EDA_Report.md 및 시각화 이미지 갱신")
        
    except Exception as e:
        print(f"[실패] EDA 분석 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
