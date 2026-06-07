# -*- coding: utf-8 -*-
"""
YES24 베스트셀러 데이터 탐색적 데이터 분석(EDA) 스크립트
작성자: 20년 경력 수석 데이터 분석가
"""

import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
import koreanize_matplotlib

# 1. 시각화 스타일 설정 (Seaborn 스타일을 사용하지 않고 vanilla matplotlib 설정을 활용하여 세련되게 커스터마이징)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.titlesize'] = 16
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['grid.alpha'] = 0.5

# 세련된 컬러 팔레트 정의 (어두운 감성 + 하이 콘트라스트)
COLORS = {
    'primary': '#1A5276',      # 차분한 네이비
    'secondary': '#E74C3C',    # 포인트 레드
    'accent': '#F39C12',       # 오렌지
    'neutral_dark': '#2C3E50', # 다크 그레이
    'neutral_light': '#BDC3C7',# 라이트 그레이
    'bg_grid': '#ECF0F1',      # 연한 배경 그리드
    'bar_color': '#3498DB',    # 스카이 블루
    'pie_colors': ['#1F618D', '#AF601A', '#239B56', '#B03A2E', '#7D3C98']
}

# 경로 설정
DATA_PATH = 'yes24/data/yes24_bestsellers.csv'
IMAGE_DIR = 'yes24/images/'
os.makedirs(IMAGE_DIR, exist_ok=True)

def load_and_profile_data():
    """데이터 로드 및 기본적인 프로파일링 정보 출력"""
    print("=== [1] 데이터 로드 및 초기 프로파일링 ===")
    df = pd.read_csv(DATA_PATH)
    
    # 5개 행씩 조회
    print("\n[상위 5개 행]")
    print(df.head())
    print("\n[하위 5개 행]")
    print(df.tail())
    
    # 기본 정보
    print("\n[데이터 구조 정보]")
    print(f"전체 행 개수: {df.shape[0]}")
    print(f"전체 열 개수: {df.shape[1]}")
    
    print("\n[데이터 타입 및 결측치 정보 (df.info)]")
    df.info()
    
    # 중복 데이터
    duplicates = df.duplicated(subset=['goods_no']).sum()
    print(f"\ngoods_no 기준 중복 행 개수: {duplicates}")
    
    return df

def clean_data(df):
    """데이터 전처리 수행"""
    print("\n=== [2] 데이터 전처리 진행 ===")
    df_clean = df.copy()
    
    # 1. 가격 컬럼 전처리 (쉼표 제거 및 숫자 변환)
    for col in ['sale_price', 'original_price']:
        if col in df_clean.columns:
            # 문자열인 경우에만 처리
            df_clean[col] = df_clean[col].astype(str).str.replace(',', '', regex=True)
            # 숫자가 아닌 문자 제거 후 수치형 변환
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0).astype(int)
            
    # 2. 포인트 컬럼 전처리 ('포인트적립1,500원' -> 1500)
    if 'point' in df_clean.columns:
        def extract_point(val):
            if pd.isna(val):
                return 0
            # 숫자만 추출
            nums = re.findall(r'\d+', str(val).replace(',', ''))
            if nums:
                return int(nums[0])
            return 0
        df_clean['point_amount'] = df_clean['point'].apply(extract_point)
    else:
        df_clean['point_amount'] = 0

    # 3. 출판일 컬럼 전처리 ('2025년 12월' -> 연도와 월 추출)
    if 'publish_date' in df_clean.columns:
        def parse_year(val):
            if pd.isna(val):
                return np.nan
            match = re.search(r'(\d{4})년', str(val))
            return int(match.group(1)) if match else np.nan

        def parse_month(val):
            if pd.isna(val):
                return np.nan
            match = re.search(r'(\d{1,2})월', str(val))
            return int(match.group(1)) if match else np.nan
            
        df_clean['publish_year'] = df_clean['publish_date'].apply(parse_year)
        df_clean['publish_month'] = df_clean['publish_date'].apply(parse_month)
    else:
        df_clean['publish_year'] = np.nan
        df_clean['publish_month'] = np.nan

    # 4. 분철 서비스 여부 전처리 (결측치는 'N'으로 대체)
    if 'spring_service' in df_clean.columns:
        df_clean['spring_service'] = df_clean['spring_service'].fillna('N').str.upper().str.strip()
        df_clean['spring_service'] = df_clean['spring_service'].apply(lambda x: 'Y' if x == 'Y' else 'N')
    else:
        df_clean['spring_service'] = 'N'

    # 5. 수치형 컬럼 자료형 강제 변환 (결측치는 0 또는 평균값 대체)
    for col in ['sale_index', 'review_count', 'rating']:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
            if col in ['sale_index', 'review_count']:
                df_clean[col] = df_clean[col].astype(int)
            else:
                df_clean[col] = df_clean[col].astype(float)

    print("전처리 완료 후 데이터 정보:")
    print(df_clean[['sale_price', 'original_price', 'point_amount', 'publish_year', 'publish_month', 'spring_service', 'sale_index', 'review_count', 'rating']].describe())
    
    return df_clean

def run_descriptive_stats(df):
    """기술 통계 요약 및 분석 리포트 생성을 위한 원천 데이터 출력"""
    print("\n=== [3] 기술통계 상세 분석 ===")
    
    # 1. 수치형 변수 기술통계량
    num_cols = ['sale_price', 'original_price', 'point_amount', 'sale_index', 'review_count', 'rating']
    num_desc = df[num_cols].describe()
    print("\n[수치형 변수 기술통계표]")
    print(num_desc)
    
    # 왜도(Skewness) 및 첨도(Kurtosis) 확인하여 분포 비대칭성 파악
    print("\n[수치형 변수 왜도(Skewness)]")
    print(df[num_cols].skew())
    
    # 2. 범주형 변수 기술통계량
    cat_cols = ['goods_type', 'publisher', 'author', 'spring_service']
    print("\n[범주형 변수 요약]")
    for col in cat_cols:
        if col in df.columns:
            print(f"\n* 컬럼명: {col}")
            print(f"고유값 수: {df[col].nunique()}")
            print(df[col].value_counts().head(10))
            
    # 상관관계 계수
    print("\n[수치형 변수 간 상관계수 행렬]")
    corr_matrix = df[num_cols].corr()
    print(corr_matrix)

def generate_visualizations(df):
    """13가지 시각화 그래프 생성 및 저장"""
    print("\n=== [4] 시각화 그래프 생성 및 저장 ===")
    
    # 그래프 1: 도서 판매가(sale_price) 분포
    plt.figure(figsize=(10, 6))
    df['sale_price'].plot(kind='hist', bins=30, color=COLORS['primary'], edgecolor='black', alpha=0.8)
    plt.title('베스트셀러 도서 판매가(sale_price) 분포')
    plt.xlabel('판매가 (원)')
    plt.ylabel('도서 수 (권)')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, 'plot1_sale_price_dist.png'))
    plt.close()
    
    # 그래프 2: 판매지수(sale_index) 분포 (Box plot)
    plt.figure(figsize=(10, 6))
    plt.boxplot(df['sale_index'], vert=False, patch_artist=True,
                boxprops=dict(facecolor=COLORS['bar_color'], color='black'),
                medianprops=dict(color=COLORS['secondary'], linewidth=2))
    plt.title('판매지수(sale_index) 상자 그림 분포')
    plt.xlabel('판매지수')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, 'plot2_sale_index_box.png'))
    plt.close()
    
    # 그래프 3: 도서 평점(rating) 분포
    plt.figure(figsize=(10, 6))
    # 평점이 0인 것은 신간이거나 리뷰가 없는 도서이므로 제외하고 분포 시각화
    rating_filtered = df[df['rating'] > 0]['rating']
    rating_filtered.plot(kind='hist', bins=20, color='#27AE60', edgecolor='black', alpha=0.8)
    plt.title('도서 평점(rating) 분포 (평점 0점 제외)')
    plt.xlabel('평점')
    plt.ylabel('도서 수 (권)')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, 'plot3_rating_dist.png'))
    plt.close()
    
    # 그래프 4: 리뷰 수(review_count) 분포
    plt.figure(figsize=(10, 6))
    df['review_count'].plot(kind='hist', bins=30, color=COLORS['accent'], edgecolor='black', alpha=0.8)
    plt.title('도서 리뷰 수(review_count) 분포')
    plt.xlabel('리뷰 수 (개)')
    plt.ylabel('도서 수 (권)')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, 'plot4_review_count_dist.png'))
    plt.close()
    
    # 그래프 5: 분철 서비스 제공 여부(spring_service) 비율 (원형 차트)
    plt.figure(figsize=(8, 8))
    spring_counts = df['spring_service'].value_counts()
    plt.pie(spring_counts, labels=spring_counts.index, autopct='%1.1f%%', startangle=90,
            colors=[COLORS['primary'], COLORS['secondary']],
            wedgeprops={'edgecolor': 'white', 'linewidth': 2, 'antialiased': True})
    plt.title('분철 서비스 제공 여부(spring_service) 비율')
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, 'plot5_spring_service_pie.png'))
    plt.close()
    
    # 그래프 6: 베스트셀러 등록 도서 수가 가장 많은 출판사 Top 30
    plt.figure(figsize=(12, 8))
    top_publishers = df['publisher'].value_counts().head(30)
    top_publishers.sort_values(ascending=True).plot(kind='barh', color=COLORS['primary'], edgecolor='black', alpha=0.9)
    plt.title('베스트셀러 등록 도서 수 상위 30대 출판사')
    plt.xlabel('등록 도서 수 (권)')
    plt.ylabel('출판사명')
    plt.grid(True, axis='x', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, 'plot6_top_publishers.png'))
    plt.close()
    
    # 그래프 7: 베스트셀러 등록 도서 수가 가장 많은 저자 Top 30
    plt.figure(figsize=(12, 8))
    top_authors = df['author'].value_counts().head(30)
    top_authors.sort_values(ascending=True).plot(kind='barh', color='#8E44AD', edgecolor='black', alpha=0.9)
    plt.title('베스트셀러 등록 도서 수 상위 30대 저자')
    plt.xlabel('등록 도서 수 (권)')
    plt.ylabel('저자명')
    plt.grid(True, axis='x', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, 'plot7_top_authors.png'))
    plt.close()
    
    # 그래프 8: 도서 정가(original_price)와 판매지수(sale_index)의 산점도
    plt.figure(figsize=(10, 6))
    plt.scatter(df['original_price'], df['sale_index'], color=COLORS['neutral_dark'], alpha=0.6, edgecolors='none')
    plt.title('도서 정가(original_price)와 판매지수(sale_index)의 산점도')
    plt.xlabel('정가 (원)')
    plt.ylabel('판매지수')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, 'plot8_price_vs_sale_index.png'))
    plt.close()
    
    # 그래프 9: 평점(rating)과 리뷰 수(review_count)의 산점도
    plt.figure(figsize=(10, 6))
    # 평점 0점(신간 등)은 왜곡을 줄이기 위해 제외하고 산점도 구성
    filtered_df = df[df['rating'] > 0]
    plt.scatter(filtered_df['rating'], filtered_df['review_count'], color='#16A085', alpha=0.7, edgecolors='none')
    plt.title('평점(rating)과 리뷰 수(review_count)의 상관 산점도')
    plt.xlabel('평점')
    plt.ylabel('리뷰 수 (개)')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, 'plot9_rating_vs_reviews.png'))
    plt.close()
    
    # 그래프 10: 분철 서비스 제공 여부(spring_service)에 따른 판매지수(sale_index) 비교
    plt.figure(figsize=(10, 6))
    groups = [df[df['spring_service'] == 'Y']['sale_index'], df[df['spring_service'] == 'N']['sale_index']]
    plt.boxplot(groups, labels=['분철 서비스 제공 (Y)', '분철 서비스 미제공 (N)'], vert=True, patch_artist=True,
                boxprops=dict(facecolor='#D35400', color='black'),
                medianprops=dict(color='black', linewidth=2))
    plt.title('분철 서비스 제공 여부에 따른 판매지수(sale_index) 비교')
    plt.ylabel('판매지수')
    plt.grid(True, axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, 'plot10_spring_vs_sale_index.png'))
    plt.close()
    
    # 그래프 11: 출판 연도 및 월별 베스트셀러 도서 출판 추이 (시계열)
    plt.figure(figsize=(12, 6))
    # 연월 결합 문자열 생성 (예: '2025-12')
    df_temp = df.dropna(subset=['publish_year', 'publish_month']).copy()
    df_temp['publish_year'] = df_temp['publish_year'].astype(int)
    df_temp['publish_month'] = df_temp['publish_month'].astype(int)
    df_temp['publish_ym'] = df_temp['publish_year'].astype(str) + '-' + df_temp['publish_month'].astype(str).str.zfill(2)
    
    ym_counts = df_temp['publish_ym'].value_counts().sort_index()
    # 최근 트렌드를 보기 위해 최근 24개월 혹은 전체 추이 시각화
    ym_counts.plot(kind='line', marker='o', color=COLORS['primary'], linewidth=2, markersize=6)
    plt.title('출판 연월별 베스트셀러 도서 출판 빈도 추이')
    plt.xlabel('출판 연월 (Year-Month)')
    plt.ylabel('출판 도서 수 (권)')
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, 'plot11_publish_trend.png'))
    plt.close()
    
    # 그래프 12: 상관계수 히트맵 (Correlation Heatmap)
    # Seaborn을 사용하지 않고 matplotlib의 matshow를 이용해 시인성 높은 히트맵 구현
    num_cols = ['sale_price', 'original_price', 'point_amount', 'sale_index', 'review_count', 'rating']
    corr = df[num_cols].corr()
    
    fig, ax = plt.subplots(figsize=(10, 8))
    cax = ax.matshow(corr, cmap='coolwarm', vmin=-1, vmax=1)
    fig.colorbar(cax)
    
    # 축 설정
    ticks = np.arange(0, len(num_cols), 1)
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.set_xticklabels(num_cols, rotation=45, ha='left')
    ax.set_yticklabels(num_cols)
    
    # 상관계수 값 텍스트 표시
    for i in range(len(num_cols)):
        for j in range(len(num_cols)):
            text = ax.text(j, i, f"{corr.iloc[i, j]:.2f}",
                           ha="center", va="center", color="black" if abs(corr.iloc[i, j]) < 0.7 else "white",
                           fontweight='bold')
                           
    plt.title('수치형 변수 간의 상관계수 히트맵', y=1.15)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, 'plot12_corr_heatmap.png'))
    plt.close()
    
    print("모든 시각화 그래프 파일이 'yes24/images/' 디렉토리에 정상 저장되었습니다.")

def run_text_analysis(df):
    """TF-IDF 기반 도서명 및 태그 주요 키워드 분석"""
    print("\n=== [5] TF-IDF 기반 텍스트 분석 ===")
    
    # 도서명과 태그 데이터를 결합하여 하나의 말뭉치 구성
    text_data = []
    for idx, row in df.iterrows():
        title = str(row['goods_name']) if not pd.isna(row['goods_name']) else ''
        subtitle = str(row['goods_subtitle']) if not pd.isna(row['goods_subtitle']) else ''
        tags = str(row['tags']) if not pd.isna(row['tags']) else ''
        
        # 특수문자 제거 및 단어 결합
        combined = f"{title} {subtitle} {tags.replace('#', ' ')}"
        # 한글, 영문, 숫자만 남기고 전처리
        cleaned = re.sub(r'[^가-힣a-zA-Z0-9\s]', ' ', combined)
        text_data.append(cleaned)
        
    # TF-IDF 분석 수행 (단어 단위 분석, 불용어 등을 고려하여 영어/한글 혼합)
    # 한국어 조사 등 의미 없는 한 글자 단어 배제를 위해 token_pattern 설정
    vectorizer = TfidfVectorizer(token_pattern=r'\b[가-힣a-zA-Z0-9]{2,}\b', max_features=100)
    tfidf_matrix = vectorizer.fit_transform(text_data)
    
    # 전체 말뭉치에 대한 각 키워드의 평균 TF-IDF 점수 산출
    feature_names = vectorizer.get_feature_names_out()
    mean_tfidf = tfidf_matrix.mean(axis=0).A1
    
    # DataFrame 생성 및 정렬
    keyword_df = pd.DataFrame({'keyword': feature_names, 'tfidf_score': mean_tfidf})
    keyword_df = keyword_df.sort_values(by='tfidf_score', ascending=False).head(30)
    
    print("\n[TF-IDF 상위 30개 핵심 키워드]")
    print(keyword_df)
    
    # 그래프 13: TF-IDF 기반 도서명/태그 주요 키워드 Top 30 시각화
    plt.figure(figsize=(12, 8))
    keyword_df.sort_values(by='tfidf_score', ascending=True).plot(
        x='keyword', y='tfidf_score', kind='barh', color='#E67E22', edgecolor='black', alpha=0.9, legend=False
    )
    plt.title('도서명 및 태그 내 주요 키워드 TF-IDF 점수 Top 30')
    plt.xlabel('TF-IDF 평균 점수')
    plt.ylabel('키워드')
    plt.grid(True, axis='x', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGE_DIR, 'plot13_text_tfidf.png'))
    plt.close()
    
    # 보고서 작성에 사용할 키워드 데이터 반환
    return keyword_df

def main():
    # 1. 데이터 프로파일링
    df_raw = load_and_profile_data()
    
    # 2. 데이터 전처리
    df_cleaned = clean_data(df_raw)
    
    # 3. 기술통계량 출력 및 상관관계 연산
    run_descriptive_stats(df_cleaned)
    
    # 4. 12개 기본 시각화 생성 및 이미지 저장
    generate_visualizations(df_cleaned)
    
    # 5. TF-IDF 기반 텍스트 분석 및 13번째 시각화 저장
    keyword_df = run_text_analysis(df_cleaned)
    
    # 통계 보고서 작성을 돕기 위해 정제된 데이터를 새로운 CSV 파일로 내보냄
    df_cleaned.to_csv('yes24/data/yes24_bestsellers_cleaned.csv', index=False, encoding='utf-8-sig')
    print("\n전처리된 데이터를 'yes24/data/yes24_bestsellers_cleaned.csv'로 저장하였습니다.")
    print("분석 작업이 모두 완료되었습니다.")

if __name__ == '__main__':
    main()
