"""
iHerb 비타민D 제품 수집 데이터 검증 스크립트

목적:
    - collect_all_pages.py 실행 후 SQLite DB의 데이터 품질을 검증합니다.
    - 수집 건수, NULL 비율, 중복 여부, 가격 분포, 평점 분포 등을 점검합니다.

실행:
    uv run src/verify_scraped_data.py
"""

import sqlite3
import pandas as pd
import pathlib
from datetime import datetime

DB_PATH    = "data/iherb_vitamind.sqlite"
TABLE_NAME = "products"


def main():
    print("=" * 60)
    print("🔍 iHerb 비타민D 수집 데이터 검증")
    print(f"   DB: {DB_PATH}")
    print(f"   시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if not pathlib.Path(DB_PATH).exists():
        print(f"\n❌ DB 파일이 없습니다: {DB_PATH}")
        print("   → collect_all_pages.py를 먼저 실행하세요.")
        return

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn)
    conn.close()

    if df.empty:
        print("\n❌ DB에 데이터가 없습니다.")
        return

    # ── 1. 기본 통계 ──────────────────────────────────────────
    print(f"\n📊 기본 통계")
    print(f"  전체 레코드 수  : {len(df):,}개")
    print(f"  수집 페이지 범위: {df['page_no'].min()} ~ {df['page_no'].max()} 페이지")
    print(f"  수집 시작 시각  : {df['collected_at'].min()}")
    print(f"  수집 종료 시각  : {df['collected_at'].max()}")

    # ── 2. 중복 검사 ──────────────────────────────────────────
    print(f"\n🔁 중복 검사")
    중복수 = df.duplicated(subset=["product_id"]).sum()
    중복OK = (중복수 == 0)
    print(f"  {'✅' if 중복OK else '❌'} 중복 product_id: {중복수}개")

    중복URL = df.duplicated(subset=["product_url"]).sum()
    print(f"  {'✅' if 중복URL == 0 else '⚠️ '} 중복 product_url: {중복URL}개")

    # ── 3. NULL 비율 ──────────────────────────────────────────
    print(f"\n🕳️  NULL 비율 검사")
    필드목록 = ["product_id", "title", "brand", "price", "rating",
               "review_count", "product_url", "image_url"]
    for 필드 in 필드목록:
        null수 = df[필드].isna().sum()
        null률 = null수 / len(df) * 100
        기준 = 5.0 if 필드 == "price" else 1.0
        OK = (null률 <= 기준)
        print(f"  {'✅' if OK else '⚠️ '} {필드:15s}: NULL {null수}개 ({null률:.1f}%)")

    # ── 4. 가격 분포 ──────────────────────────────────────────
    print(f"\n💰 가격 분포 (원)")
    가격 = df["price"].dropna()
    if not 가격.empty:
        print(f"  최소가   : {가격.min():,}원")
        print(f"  중앙값   : {가격.median():,.0f}원")
        print(f"  평균가   : {가격.mean():,.0f}원")
        print(f"  최대가   : {가격.max():,}원")
        이상값수 = (가격 <= 0).sum()
        print(f"  {'✅' if 이상값수 == 0 else '⚠️ '} 0원 이하 이상값: {이상값수}개")

    # ── 5. 평점 분포 ──────────────────────────────────────────
    print(f"\n⭐ 평점 분포")
    평점 = df["rating"].dropna()
    if not 평점.empty:
        print(f"  최저 평점: {평점.min()}")
        print(f"  평균 평점: {평점.mean():.2f}")
        print(f"  최고 평점: {평점.max()}")
        범위이탈 = ((평점 < 0) | (평점 > 5)).sum()
        print(f"  {'✅' if 범위이탈 == 0 else '⚠️ '} 범위 이탈(0~5 밖): {범위이탈}개")

    # ── 6. 브랜드 Top 10 ──────────────────────────────────────
    print(f"\n🏆 브랜드 Top 10")
    브랜드_집계 = df["brand"].value_counts().head(10)
    for 브랜드, 수량 in 브랜드_집계.items():
        print(f"  {브랜드:35s}: {수량:3d}개")

    # ── 7. 페이지별 수집 건수 ─────────────────────────────────
    print(f"\n📄 페이지별 수집 건수")
    페이지_집계 = df.groupby("page_no").size()
    for 페이지, 수량 in 페이지_집계.items():
        이상 = (수량 < 10)
        print(f"  {'⚠️ ' if 이상 else '   '} page={페이지:3d}: {수량}개")

    # ── 8. 종합 판정 ──────────────────────────────────────────
    print(f"\n{'=' * 60}")
    전체OK = (중복수 == 0 and len(df) > 0)
    if 전체OK:
        print("✅ 데이터 검증 통과! 수집 데이터가 양호합니다.")
    else:
        print("⚠️  일부 항목이 기준을 벗어났습니다. 위 결과를 검토하세요.")
    print(f"{'=' * 60}")

    # ── 9. 샘플 데이터 출력 ───────────────────────────────────
    print(f"\n📋 샘플 데이터 (상위 5개)")
    표시컬럼 = ["product_id", "brand", "price", "rating", "review_count"]
    print(df[표시컬럼].head(5).to_string(index=False))


if __name__ == "__main__":
    main()
