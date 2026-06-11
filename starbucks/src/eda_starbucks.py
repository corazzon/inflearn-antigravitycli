"""
스타벅스 매장 데이터를 분석하기 위한 EDA(탐색적 데이터 분석) 스크립트입니다.
이 스크립트는 수집된 스타벅스 매장 데이터(starbucks_stores.csv)를 로드하고,
기본 통계량 분석, 10개 이상의 데이터 시각화 이미지 생성, 
그리고 매장명에 대한 TF-IDF 핵심 키워드 분석을 수행합니다.
시각화 결과는 starbucks/images 디렉토리에 저장됩니다.
"""
import os
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
import koreanize_matplotlib

# 1. 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "../data/starbucks_stores.csv")
IMAGE_DIR = os.path.join(BASE_DIR, "../images")
os.makedirs(IMAGE_DIR, exist_ok=True)

# 2. 데이터 로드
print("--- [데이터 로드 및 기본 파악] ---")
df = pd.read_csv(DATA_PATH)

print(f"데이터 크기 (행, 열): {df.shape}")
print(f"중복 데이터 수: {df.duplicated().sum()}")
print("\n[head() 5개 행]")
print(df.head().to_markdown())
print("\n[tail() 5개 행]")
print(df.tail().to_markdown())

print("\n[데이터 기본 정보 (info)]")
df.info()

# 3. 데이터 전처리
# '오픈일자'를 datetime 형태로 변환
df['오픈일자'] = pd.to_datetime(df['오픈일자'].astype(str), format='%Y%m%d', errors='coerce')
df['오픈연도'] = df['오픈일자'].dt.year
df['오픈월'] = df['오픈일자'].dt.month
df['오픈요일'] = df['오픈일자'].dt.dayofweek # 0=월, 6=일
weekday_map = {0: '월', 1: '화', 2: '수', 3: '목', 4: '금', 5: '토', 6: '일'}
df['오픈요일한글'] = df['오픈요일'].map(weekday_map)

# 4. 기술통계 분석
print("\n--- [기술통계 - 수치형 변수] ---")
print(df.describe().to_markdown())

print("\n--- [기술통계 - 범주형 변수] ---")
# 수치형이 아닌 범주형 대상 컬럼 필터링
cat_cols = ['시도명', '구군명', '테마매장여부', '오픈요일한글']
print(df[cat_cols].describe(include='all').to_markdown())

# 시각화 설정 공통 함수 (seaborn 전역 스타일 지정 금지 준수)
def setup_plot(title, xlabel, ylabel, figsize=(10, 6)):
    plt.figure(figsize=figsize)
    plt.title(title, fontsize=14, fontweight='bold', pad=15)
    plt.xlabel(xlabel, fontsize=12, labelpad=10)
    plt.ylabel(ylabel, fontsize=12, labelpad=10)
    plt.grid(True, linestyle='--', alpha=0.5)

# ==========================================
# 시각화 10개 및 매핑 통계표 출력
# ==========================================

# 1. [일변량] 시도명 분포 (시도별 매장 수)
setup_plot("전국 시도별 스타벅스 매장 수 분포", "시도명", "매장 수")
sido_counts = df['시도명'].value_counts()
sns.barplot(x=sido_counts.index, y=sido_counts.values, palette="viridis", hue=sido_counts.index, legend=False)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "01_sido_distribution.png"), dpi=150)
plt.close()
print("\n--- [표 1] 시도별 매장 수 ---")
print(sido_counts.to_frame('매장수').to_markdown())

# 2. [일변량] 오픈 연도별 매장 개설 트렌드 (연도별 개점 매장 수)
setup_plot("연도별 스타벅스 신규 개점 수 추이", "개점 연도", "신규 개점 수")
# 오픈연도가 Null이 아닌 데이터 대상
yearly_counts = df['오픈연도'].dropna().value_counts().sort_index()
plt.plot(yearly_counts.index, yearly_counts.values, marker='o', color='#006241', linewidth=2)
plt.xticks(yearly_counts.index, rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "02_yearly_openings.png"), dpi=150)
plt.close()
print("\n--- [표 2] 연도별 신규 개점 수 ---")
print(yearly_counts.to_frame('개점수').to_markdown())

# 3. [일변량] 오픈 월별 계절성 분석 (월별 개점 매장 수)
setup_plot("월별 스타벅스 신규 개점 수 분포", "개점 월", "신규 개점 수")
monthly_counts = df['오픈월'].dropna().value_counts().sort_index().astype(int)
sns.barplot(x=monthly_counts.index.astype(int), y=monthly_counts.values, color='#8E7A5F')
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "03_monthly_openings.png"), dpi=150)
plt.close()
print("\n--- [표 3] 월별 신규 개점 수 ---")
print(monthly_counts.to_frame('개점수').to_markdown())

# 4. [일변량] 오픈 요일별 분석 (요일별 개점 매장 수)
setup_plot("요일별 스타벅스 신규 개점 수 분포", "요일", "신규 개점 수")
weekday_order = ['월', '화', '수', '목', '금', '토', '일']
weekday_counts = df['오픈요일한글'].value_counts().reindex(weekday_order)
sns.barplot(x=weekday_counts.index, y=weekday_counts.values, palette="copper", hue=weekday_counts.index, legend=False)
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "04_weekday_openings.png"), dpi=150)
plt.close()
print("\n--- [표 4] 요일별 신규 개점 수 ---")
print(weekday_counts.to_frame('개점수').to_markdown())

# 5. [이변량] 서울시 구군별 매장 분포 (서울시 내 구군별 매장 수)
seoul_df = df[df['시도명'] == '서울']
seoul_gugun_counts = seoul_df['구군명'].value_counts()
setup_plot("서울시 구군별 스타벅스 매장 수 분포", "구군명", "매장 수", figsize=(12, 6))
sns.barplot(x=seoul_gugun_counts.index, y=seoul_gugun_counts.values, palette="magma", hue=seoul_gugun_counts.index, legend=False)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "05_seoul_gugun_distribution.png"), dpi=150)
plt.close()
print("\n--- [표 5] 서울시 구군별 매장 수 ---")
print(seoul_gugun_counts.to_frame('매장수').to_markdown())

# 6. [이변량] 시도명별 위도(Latitude) 분포 (지리적 위도 분포)
setup_plot("시도별 스타벅스 매장 위도(Latitude) 분포", "시도명", "위도", figsize=(12, 6))
sns.boxplot(x='시도명', y='위도', data=df, palette="Set3", hue='시도명', legend=False)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "06_sido_latitude_boxplot.png"), dpi=150)
plt.close()
print("\n--- [표 6] 시도별 위도 기술통계 요약 ---")
print(df.groupby('시도명')['위도'].describe().to_markdown())

# 7. [이변량] 오픈 연도와 월의 교차 분포 (개점 수 변화 추이)
pivot_df = df.pivot_table(index='오픈연도', columns='오픈월', values='매장명', aggfunc='count', fill_value=0)
# 최근 10개년만 시각화 (너무 길어지는 것을 방지)
recent_years = sorted(df['오픈연도'].dropna().unique())[-10:]
pivot_recent = pivot_df.loc[recent_years]
plt.figure(figsize=(12, 8))
plt.title("최근 10개년 연도별-월별 신규 개점 수 히트맵", fontsize=14, fontweight='bold', pad=15)
sns.heatmap(pivot_recent, annot=True, fmt="d", cmap="YlGn", cbar=True, linewidths=0.5)
plt.xlabel("개점 월", fontsize=12)
plt.ylabel("개점 연도", fontsize=12)
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "07_yearly_monthly_heatmap.png"), dpi=150)
plt.close()
print("\n--- [표 7] 최근 10개년 연도별-월별 신규 개점 수 ---")
print(pivot_recent.to_markdown())

# 8. [다변량] 주요 5대 시도(서울, 경기, 부산, 대구, 인천)의 연도별 누적 매장 수 추이
top_sidos = ['서울', '경기', '부산', '대구', '인천']
filtered_sido_df = df[df['시도명'].isin(top_sidos)].dropna(subset=['오픈연도'])
# 연도별 개점 수 계산 후 누적합 계산
sido_yearly_size = filtered_sido_df.groupby(['시도명', '오픈연도']).size().unstack(fill_value=0)
sido_cumulative = sido_yearly_size.cumsum(axis=1)

setup_plot("주요 5대 시도별 스타벅스 누적 매장 수 추이", "개점 연도", "누적 매장 수", figsize=(12, 6))
for sido in top_sidos:
    if sido in sido_cumulative.index:
        plt.plot(sido_cumulative.columns, sido_cumulative.loc[sido], marker='o', label=sido, linewidth=2)
plt.legend(title="시도명")
plt.xticks(sido_cumulative.columns, rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "08_sido_cumulative_trend.png"), dpi=150)
plt.close()
print("\n--- [표 8] 주요 5대 시도별 연도별 누적 매장 수 (일부 연도) ---")
print(sido_cumulative.iloc[:, -10:].to_markdown()) # 최근 10개년만 출력

# 9. [다변량] 서울 주요 3대 구(강남, 서초, 송파)의 연도별 신규 개점 수 비교
gangnam3 = ['강남구', '서초구', '송파구']
seoul_gangnam3_df = seoul_df[seoul_df['구군명'].isin(gangnam3)].dropna(subset=['오픈연도'])
gangnam3_yearly = seoul_gangnam3_df.groupby(['구군명', '오픈연도']).size().unstack(fill_value=0)

setup_plot("서울 강남 3구 연도별 신규 개점 매장 수 비교", "개점 연도", "신규 개점 수", figsize=(12, 6))
for gugun in gangnam3:
    if gugun in gangnam3_yearly.index:
        plt.plot(gangnam3_yearly.columns, gangnam3_yearly.loc[gugun], marker='s', label=gugun, linewidth=2)
plt.legend(title="구군명")
plt.xticks(gangnam3_yearly.columns, rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "09_seoul_gangnam3_yearly.png"), dpi=150)
plt.close()
print("\n--- [표 9] 서울 강남 3구 연도별 신규 개점 수 (일부 연도) ---")
print(gangnam3_yearly.iloc[:, -10:].to_markdown())

# 10. [텍스트 - TF-IDF] 매장명 텍스트에서 추출한 핵심 키워드 중요도 (상위 30개)
# TfidfVectorizer를 사용하여 분석
# 한국어 형태소 분석기 없이 띄어쓰기 기준으로 단어 토큰화
vectorizer = TfidfVectorizer(token_pattern=r'(?u)\b\w+\b', max_features=1000)
tfidf_matrix = vectorizer.fit_transform(df['매장명'].fillna(''))
feature_names = vectorizer.get_feature_names_out()
# 각 단어들의 TF-IDF 평균값 계산
tfidf_means = np.mean(tfidf_matrix.toarray(), axis=0)
tfidf_df = pd.DataFrame({'keyword': feature_names, 'tfidf_weight': tfidf_means})
tfidf_top30 = tfidf_df.sort_values(by='tfidf_weight', ascending=False).head(30)

setup_plot("스타벅스 매장명 핵심 키워드 중요도 (TF-IDF 상위 30개)", "TF-IDF 평균 가중치", "키워드", figsize=(12, 8))
sns.barplot(x='tfidf_weight', y='keyword', data=tfidf_top30, palette="GnBu_r", hue='keyword', legend=False)
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "10_store_name_tfidf.png"), dpi=150)
plt.close()

print("\n--- [표 10] 매장명 TF-IDF 키워드 상위 30개 및 가중치 ---")
print(tfidf_top30.reset_index(drop=True).to_markdown())

print("\nEDA 및 이미지 생성이 완료되었습니다.")
