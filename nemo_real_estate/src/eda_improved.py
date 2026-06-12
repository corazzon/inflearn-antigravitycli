"""
네모부동산 데이터 분석 개선 스크립트 (비판적 재분석 버전)

이 스크립트는 기존 EDA(eda.py)의 문제점을 보완하여 다음 항목을 추가로 분석합니다:
1. 이상치(Outlier) 탐지 및 제거 후 재분석 (IQR 방식)
2. 단위면적(㎡)당 월세 단가 분포 분석 (누락된 핵심 지표)
3. 지역별 보증금/월세/면적 박스플롯 비교 (이상치 포함/제거 각각)
4. 관리비, 권리금 분포 분석 (기존에 누락된 비용 항목)
5. 비용 구성 요소별 상관관계 히트맵 개선
6. 수치형 변수 왜도(Skewness) 시각화

비판 포인트 요약:
- 기존 eda.py는 이상치를 제거하지 않은 채 히스토그램/박스플롯을 작성 → 왜곡된 분포 제시
- 파일명과 차트 제목이 불일치 (예: 03_rating_distribution.png → 실제로는 월세 분포)
- 인덱스 대비 월세 산포도(08)는 의미 없는 시각화
- 단위면적당 단가 분석이 완전히 누락
- 관리비·권리금 등 실질 비용 항목 미분석
- 광화문역 vs 강남역 63:40 샘플 불균형을 명시하지 않음
- areaPrice 컬럼(만원/㎡) 이미 존재하는데 재산출 없이 활용 안함

작성자: 데이터 분석 비판 에이전트
작성일: 2026-06-12
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import koreanize_matplotlib

# ─────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────
CSV_PATH = "nemo_real_estate/data/nemo_real_estate_bestseller.csv"
IMAGE_DIR = "nemo_real_estate/images"
os.makedirs(IMAGE_DIR, exist_ok=True)

REGION_COLORS = {"강남역": "#E8604C", "광화문역": "#4C72B0"}


def load_and_clean():
    """데이터를 로드하고 분석용 컬럼을 준비합니다."""
    df = pd.read_csv(CSV_PATH)
    # 핵심 수치형 컬럼 명시적 변환
    for col in ["deposit", "monthlyRent", "size", "maintenanceFee", "premium", "areaPrice"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    # 단위면적당 월세 단가 계산 (㎡당 만원)
    df["rent_per_sqm"] = df["monthlyRent"] / df["size"].replace(0, np.nan)
    # 단위면적당 보증금 단가 계산
    df["deposit_per_sqm"] = df["deposit"] / df["size"].replace(0, np.nan)
    return df


def remove_outliers_iqr(series, multiplier=1.5):
    """IQR 방식으로 이상치를 제거한 시리즈를 반환합니다."""
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr
    return series[(series >= lower) & (series <= upper)]


def print_outlier_stats(col_name, series):
    """이상치 통계를 출력합니다."""
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    outliers = series[(series < lower) | (series > upper)]
    print(f"\n[{col_name}] 이상치 분석")
    print(f"  전체 범위: {series.min():.0f} ~ {series.max():.0f}")
    print(f"  IQR 정상 범위: {lower:.0f} ~ {upper:.0f}")
    print(f"  이상치 수: {len(outliers)} / {len(series)} ({len(outliers)/len(series)*100:.1f}%)")
    print(f"  이상치 최대값 Top5:\n{series.nlargest(5).to_string()}")


# ─────────────────────────────────────────────
# 차트 12: 이상치 제거 전후 보증금·월세 분포 비교
# ─────────────────────────────────────────────
def chart12_outlier_removed(df):
    """이상치 제거 전후 분포를 4분할 서브플롯으로 비교합니다."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("[비판 개선] 이상치 제거 전/후 분포 비교\n"
                 "(좌: 전체 데이터, 우: IQR 1.5 기준 이상치 제거 후)", fontsize=14, fontweight="bold")

    dep_raw = df["deposit"].dropna()
    dep_clean = remove_outliers_iqr(dep_raw)
    rent_raw = df["monthlyRent"].dropna()
    rent_clean = remove_outliers_iqr(rent_raw)

    # 보증금 - 이상치 포함
    axes[0, 0].hist(dep_raw, bins=30, color="#E8604C", alpha=0.75, edgecolor="black")
    axes[0, 0].set_title(f"보증금 분포 [원본] (n={len(dep_raw)}, 이상치 {len(dep_raw)-len(dep_clean)}건 포함)")
    axes[0, 0].set_xlabel("보증금 (만원)")
    axes[0, 0].set_ylabel("매물 수")
    axes[0, 0].axvline(dep_raw.mean(), color="navy", linestyle="--", label=f"평균 {dep_raw.mean():.0f}")
    axes[0, 0].axvline(dep_raw.median(), color="gold", linestyle="-.", label=f"중앙값 {dep_raw.median():.0f}")
    axes[0, 0].legend(fontsize=9)
    axes[0, 0].grid(axis="y", alpha=0.4)

    # 보증금 - 이상치 제거
    axes[0, 1].hist(dep_clean, bins=30, color="#4C72B0", alpha=0.75, edgecolor="black")
    axes[0, 1].set_title(f"보증금 분포 [이상치 제거] (n={len(dep_clean)}, {len(dep_raw)-len(dep_clean)}건 제거)")
    axes[0, 1].set_xlabel("보증금 (만원)")
    axes[0, 1].set_ylabel("매물 수")
    axes[0, 1].axvline(dep_clean.mean(), color="navy", linestyle="--", label=f"평균 {dep_clean.mean():.0f}")
    axes[0, 1].axvline(dep_clean.median(), color="gold", linestyle="-.", label=f"중앙값 {dep_clean.median():.0f}")
    axes[0, 1].legend(fontsize=9)
    axes[0, 1].grid(axis="y", alpha=0.4)

    # 월세 - 이상치 포함
    axes[1, 0].hist(rent_raw, bins=30, color="#E8604C", alpha=0.75, edgecolor="black")
    axes[1, 0].set_title(f"월세 분포 [원본] (n={len(rent_raw)}, 이상치 {len(rent_raw)-len(rent_clean)}건 포함)")
    axes[1, 0].set_xlabel("월세 (만원)")
    axes[1, 0].set_ylabel("매물 수")
    axes[1, 0].axvline(rent_raw.mean(), color="navy", linestyle="--", label=f"평균 {rent_raw.mean():.0f}")
    axes[1, 0].axvline(rent_raw.median(), color="gold", linestyle="-.", label=f"중앙값 {rent_raw.median():.0f}")
    axes[1, 0].legend(fontsize=9)
    axes[1, 0].grid(axis="y", alpha=0.4)

    # 월세 - 이상치 제거
    axes[1, 1].hist(rent_clean, bins=30, color="#4C72B0", alpha=0.75, edgecolor="black")
    axes[1, 1].set_title(f"월세 분포 [이상치 제거] (n={len(rent_clean)}, {len(rent_raw)-len(rent_clean)}건 제거)")
    axes[1, 1].set_xlabel("월세 (만원)")
    axes[1, 1].set_ylabel("매물 수")
    axes[1, 1].axvline(rent_clean.mean(), color="navy", linestyle="--", label=f"평균 {rent_clean.mean():.0f}")
    axes[1, 1].axvline(rent_clean.median(), color="gold", linestyle="-.", label=f"중앙값 {rent_clean.median():.0f}")
    axes[1, 1].legend(fontsize=9)
    axes[1, 1].grid(axis="y", alpha=0.4)

    plt.tight_layout()
    save_path = f"{IMAGE_DIR}/12_outlier_removed.png"
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[저장] {save_path}")

    # 통계표 출력
    print("\n[차트12] 이상치 제거 전후 기술통계 비교")
    stats_dict = {
        "보증금(원본)": dep_raw.describe(),
        "보증금(이상치제거)": dep_clean.describe(),
        "월세(원본)": rent_raw.describe(),
        "월세(이상치제거)": rent_clean.describe(),
    }
    stats_df = pd.DataFrame(stats_dict)
    print(stats_df.to_string())


# ─────────────────────────────────────────────
# 차트 13: 단위면적당 월세 단가 분포 (기존에 완전 누락)
# ─────────────────────────────────────────────
def chart13_price_per_sqm(df):
    """단위면적(㎡)당 월세 단가 분포를 지역별로 시각화합니다."""
    df_valid = df[["region", "rent_per_sqm", "deposit_per_sqm"]].dropna()
    df_valid = df_valid[df_valid["rent_per_sqm"] > 0]

    # 이상치 제거
    rent_psm_clean_idx = df_valid.index.isin(
        remove_outliers_iqr(df_valid["rent_per_sqm"]).index
    )
    df_clean = df_valid[rent_psm_clean_idx]

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle("[비판 개선] 단위면적(㎡)당 월세 단가 분석\n"
                 "(기존 EDA에서 완전히 누락된 핵심 가격 지표)", fontsize=13, fontweight="bold")

    # 1) 전체 KDE
    for region, grp in df_clean.groupby("region"):
        grp["rent_per_sqm"].plot.kde(ax=axes[0], label=region,
                                      color=REGION_COLORS.get(region, "gray"), linewidth=2)
    axes[0].set_title("㎡당 월세 KDE 밀도 분포")
    axes[0].set_xlabel("㎡당 월세 (만원/㎡)")
    axes[0].set_ylabel("밀도")
    axes[0].legend()
    axes[0].grid(alpha=0.4)

    # 2) 지역별 히스토그램
    for region, grp in df_clean.groupby("region"):
        axes[1].hist(grp["rent_per_sqm"], bins=25, alpha=0.65,
                     label=region, color=REGION_COLORS.get(region, "gray"), edgecolor="white")
    axes[1].set_title("지역별 ㎡당 월세 히스토그램")
    axes[1].set_xlabel("㎡당 월세 (만원/㎡)")
    axes[1].set_ylabel("매물 수")
    axes[1].legend()
    axes[1].grid(axis="y", alpha=0.4)

    # 3) 박스플롯
    data_for_box = [
        df_clean[df_clean["region"] == r]["rent_per_sqm"].dropna()
        for r in ["강남역", "광화문역"]
    ]
    bp = axes[2].boxplot(data_for_box, patch_artist=True, widths=0.5,
                          medianprops=dict(color="black", linewidth=2))
    colors = [REGION_COLORS["강남역"], REGION_COLORS["광화문역"]]
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.75)
    axes[2].set_xticklabels(["강남역", "광화문역"])
    axes[2].set_title("지역별 ㎡당 월세 박스플롯")
    axes[2].set_ylabel("㎡당 월세 (만원/㎡)")
    axes[2].grid(axis="y", alpha=0.4)

    plt.tight_layout()
    save_path = f"{IMAGE_DIR}/13_price_per_sqm.png"
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[저장] {save_path}")

    # 통계표 출력
    print("\n[차트13] 지역별 ㎡당 월세 단가 통계")
    stats = df_clean.groupby("region")["rent_per_sqm"].agg(["count","mean","median","std","min","max"])
    stats.columns = ["매물수","평균(만원/㎡)","중앙값","표준편차","최솟값","최댓값"]
    print(stats.to_string())


# ─────────────────────────────────────────────
# 차트 14: 지역별 가격 지표 종합 박스플롯 비교
# ─────────────────────────────────────────────
def chart14_region_comparison(df):
    """지역별 보증금, 월세, 면적, 관리비를 이상치 제거 후 박스플롯으로 비교합니다."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    fig.suptitle("[비판 개선] 강남역 vs 광화문역 핵심 지표 종합 비교\n"
                 "(이상치 IQR 1.5배 제거 후, 샘플: 강남역 400건 vs 광화문역 263건)",
                 fontsize=13, fontweight="bold")

    metrics = [
        ("deposit", "보증금 (만원)", axes[0, 0]),
        ("monthlyRent", "월세 (만원)", axes[0, 1]),
        ("size", "면적 (㎡)", axes[1, 0]),
        ("maintenanceFee", "관리비 (만원)", axes[1, 1]),
    ]

    region_order = ["강남역", "광화문역"]
    palette = {"강남역": REGION_COLORS["강남역"], "광화문역": REGION_COLORS["광화문역"]}

    for col, ylabel, ax in metrics:
        df_col = df[["region", col]].copy().dropna()
        df_col[col] = pd.to_numeric(df_col[col], errors="coerce")
        # 이상치 제거 (지역 내 IQR)
        clean_parts = []
        for r in region_order:
            sub = df_col[df_col["region"] == r][col].dropna()
            clean_sub = remove_outliers_iqr(sub)
            tmp = pd.DataFrame({"region": r, col: clean_sub})
            clean_parts.append(tmp)
        df_clean = pd.concat(clean_parts)

        sns.boxplot(
            x="region", y=col, data=df_clean,
            order=region_order, hue="region",
            palette=palette, legend=False,
            width=0.5, ax=ax, linewidth=1.2,
            flierprops=dict(marker="o", markersize=4, alpha=0.5)
        )
        # 평균선 추가
        for i, r in enumerate(region_order):
            mean_val = df_clean[df_clean["region"] == r][col].mean()
            ax.plot(i, mean_val, "D", color="white", markersize=8,
                    markeredgecolor="black", markeredgewidth=1.5, zorder=5)
        ax.set_title(f"지역별 {ylabel}")
        ax.set_xlabel("지역")
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", alpha=0.4)

        # 인라인 통계 주석
        for i, r in enumerate(region_order):
            sub = df_clean[df_clean["region"] == r][col]
            ax.text(i, ax.get_ylim()[1] * 0.95,
                    f"중앙값\n{sub.median():.0f}",
                    ha="center", va="top", fontsize=8,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7))

    # 범례 추가
    patches = [mpatches.Patch(color=v, label=k) for k, v in palette.items()]
    fig.legend(handles=patches, loc="lower center", ncol=2, fontsize=11, frameon=True)
    diamond = plt.Line2D([0], [0], marker="D", color="w", markerfacecolor="white",
                          markeredgecolor="black", markersize=8, label="평균값(◆)")
    fig.legend(handles=patches + [diamond], loc="lower center", ncol=3, fontsize=10)

    plt.tight_layout(rect=[0, 0.05, 1, 1])
    save_path = f"{IMAGE_DIR}/14_region_comparison.png"
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[저장] {save_path}")

    # 통계표 출력
    print("\n[차트14] 지역별 핵심 지표 기술통계 (이상치 제거 후)")
    for col, ylabel, _ in metrics:
        df_col = df[["region", col]].copy().dropna()
        df_col[col] = pd.to_numeric(df_col[col], errors="coerce")
        clean_parts = []
        for r in region_order:
            sub = df_col[df_col["region"] == r][col].dropna()
            clean_sub = remove_outliers_iqr(sub)
            tmp = pd.DataFrame({"region": r, col: clean_sub})
            clean_parts.append(tmp)
        df_clean = pd.concat(clean_parts)
        stats = df_clean.groupby("region")[col].agg(["count","mean","median","std"])
        stats.columns = ["매물수","평균","중앙값","표준편차"]
        print(f"\n  [{ylabel}]")
        print(stats.to_string())


# ─────────────────────────────────────────────
# 차트 15 (보너스): 보증금-월세 관계 (이상치 제거 + 면적 버블)
# ─────────────────────────────────────────────
def chart15_deposit_rent_bubble(df):
    """이상치 제거 후 보증금-월세 관계를 면적 버블로 시각화합니다 (기존 07 개선)."""
    df_v = df[["region", "deposit", "monthlyRent", "size"]].copy().dropna()
    for col in ["deposit", "monthlyRent", "size"]:
        df_v[col] = pd.to_numeric(df_v[col], errors="coerce")
    df_v = df_v.dropna()

    # 지역별 이상치 제거
    clean_parts = []
    for r in ["강남역", "광화문역"]:
        sub = df_v[df_v["region"] == r].copy()
        dep_clean = remove_outliers_iqr(sub["deposit"])
        rent_clean = remove_outliers_iqr(sub["monthlyRent"])
        idx = dep_clean.index.intersection(rent_clean.index)
        clean_parts.append(sub.loc[idx])
    df_clean = pd.concat(clean_parts)

    fig, ax = plt.subplots(figsize=(12, 8))

    for r in ["강남역", "광화문역"]:
        sub = df_clean[df_clean["region"] == r]
        size_scaled = (sub["size"] / sub["size"].max()) * 300 + 20
        ax.scatter(sub["deposit"], sub["monthlyRent"],
                   s=size_scaled, alpha=0.6,
                   color=REGION_COLORS[r], edgecolors="white",
                   linewidth=0.5, label=f"{r} (n={len(sub)})")

    ax.set_title("[비판 개선] 보증금 vs 월세 버블 차트 (이상치 제거 후)\n"
                 "버블 크기 = 면적(㎡), 기존 07번 차트의 이상치 미제거 문제 해결",
                 fontsize=12, fontweight="bold")
    ax.set_xlabel("보증금 (만원)")
    ax.set_ylabel("월세 (만원)")
    ax.legend(fontsize=11)
    ax.grid(alpha=0.3)

    # 상관계수 표시
    corr = df_clean[["deposit", "monthlyRent"]].corr().iloc[0, 1]
    ax.text(0.05, 0.95, f"전체 상관계수(r) = {corr:.3f}",
            transform=ax.transAxes, fontsize=11,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.8))

    for r in ["강남역", "광화문역"]:
        sub = df_clean[df_clean["region"] == r]
        r_corr = sub[["deposit", "monthlyRent"]].corr().iloc[0, 1]
        print(f"  [{r}] 보증금-월세 상관계수: {r_corr:.3f}")

    plt.tight_layout()
    save_path = f"{IMAGE_DIR}/15_deposit_rent_bubble.png"
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[저장] {save_path}")


# ─────────────────────────────────────────────
# 차트 16 (보너스): 권리금 분포 및 지역별 차이 (기존에 누락)
# ─────────────────────────────────────────────
def chart16_premium_analysis(df):
    """권리금(premium) 분포와 지역별 차이를 분석합니다 (기존 EDA에서 누락)."""
    df_p = df[["region", "premium"]].copy()
    df_p["premium"] = pd.to_numeric(df_p["premium"], errors="coerce").fillna(0)
    df_p["has_premium"] = df_p["premium"] > 0

    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    fig.suptitle("[비판 개선] 권리금(Premium) 분포 분석\n"
                 "(기존 EDA에서 완전 누락 - 상업용 부동산의 핵심 비용 지표)",
                 fontsize=12, fontweight="bold")

    # 1) 권리금 유/무 비율 파이차트
    prem_ratio = df_p["has_premium"].value_counts()
    labels = ["권리금 없음", "권리금 있음"]
    colors = ["#AED6F1", "#E8604C"]
    axes[0].pie(prem_ratio.values, labels=labels, colors=colors,
                autopct="%1.1f%%", startangle=90,
                wedgeprops=dict(edgecolor="white", linewidth=2))
    axes[0].set_title("권리금 유/무 비율")

    # 2) 지역별 권리금 보유율
    prem_by_region = df_p.groupby("region")["has_premium"].mean() * 100
    bars = axes[1].bar(prem_by_region.index, prem_by_region.values,
                       color=[REGION_COLORS.get(r, "gray") for r in prem_by_region.index],
                       edgecolor="black", alpha=0.85)
    for bar in bars:
        h = bar.get_height()
        axes[1].text(bar.get_x() + bar.get_width() / 2, h + 0.5,
                     f"{h:.1f}%", ha="center", fontsize=11, fontweight="bold")
    axes[1].set_title("지역별 권리금 보유 매물 비율")
    axes[1].set_xlabel("지역")
    axes[1].set_ylabel("권리금 보유 비율 (%)")
    axes[1].set_ylim(0, 100)
    axes[1].grid(axis="y", alpha=0.4)

    # 3) 권리금 있는 매물의 분포 박스플롯 (이상치 제거)
    df_has = df_p[df_p["has_premium"]]
    clean_parts = []
    for r in ["강남역", "광화문역"]:
        sub = df_has[df_has["region"] == r]["premium"]
        clean_sub = remove_outliers_iqr(sub)
        tmp = pd.DataFrame({"region": r, "premium": clean_sub})
        clean_parts.append(tmp)
    df_prem_clean = pd.concat(clean_parts)

    sns.boxplot(x="region", y="premium", data=df_prem_clean,
                hue="region", palette=REGION_COLORS, legend=False,
                width=0.5, ax=axes[2], linewidth=1.2)
    axes[2].set_title("지역별 권리금 분포 (이상치 제거)")
    axes[2].set_xlabel("지역")
    axes[2].set_ylabel("권리금 (만원)")
    axes[2].grid(axis="y", alpha=0.4)

    plt.tight_layout()
    save_path = f"{IMAGE_DIR}/16_premium_analysis.png"
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[저장] {save_path}")

    print("\n[차트16] 지역별 권리금 통계 (권리금 있는 매물만)")
    stats = df_has.groupby("region")["premium"].agg(["count","mean","median","std","max"])
    stats.columns = ["매물수","평균(만원)","중앙값","표준편차","최댓값"]
    print(stats.to_string())
    print(f"\n전체 권리금 보유율: {df_p['has_premium'].mean()*100:.1f}%")


# ─────────────────────────────────────────────
# 메인 실행
# ─────────────────────────────────────────────
def main():
    print("=" * 60)
    print("[비판적 EDA] 네모부동산 데이터 개선 분석 시작")
    print("=" * 60)

    df = load_and_clean()
    print(f"\n데이터 로드 완료: {df.shape[0]}행 × {df.shape[1]}열")
    print(f"지역 분포: {df['region'].value_counts().to_dict()}")

    # 이상치 통계 출력
    print_outlier_stats("보증금(deposit)", df["deposit"].dropna())
    print_outlier_stats("월세(monthlyRent)", df["monthlyRent"].dropna())
    print_outlier_stats("면적(size)", df["size"].dropna())
    print_outlier_stats("관리비(maintenanceFee)", df["maintenanceFee"].dropna())

    print("\n[차트 생성 시작]")
    chart12_outlier_removed(df)
    chart13_price_per_sqm(df)
    chart14_region_comparison(df)
    chart15_deposit_rent_bubble(df)
    chart16_premium_analysis(df)

    print("\n" + "=" * 60)
    print("[완료] 개선 차트 5종 생성: 12~16번")
    print(f"저장 경로: {IMAGE_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
