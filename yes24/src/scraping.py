# -*- coding: utf-8 -*-
"""
YES24 베스트셀러 카테고리 도서 정보 스크래핑 모듈

이 모듈은 YES24의 베스트셀러 카테고리 비동기 API(BestSellerContents)를 활용하여
도서 목록을 마지막 페이지까지 크롤링하고 수집한 데이터를 CSV 파일로 저장하는 역할을 합니다.

주요 기능:
- 지정된 카테고리 번호의 베스트셀러 도서 목록 수집
- 페이지 간 대기 시간(0.1 ~ 0.5초)을 두어 서버 과부하 및 차단 예방
- 기존에 수집된 CSV 파일이 존재할 경우, 중복을 방지하며 2페이지부터 이어서 수집(append)
- 도서명, 저자, 출판사, 가격, 판매지수, 평점 등 다양한 도서 상세 정보 정밀 파싱
- 수집된 최종 데이터를 Pandas DataFrame을 통해 CSV 파일('utf-8-sig' 인코딩)로 안전하게 저장

작성자: Antigravity AI
생성일: 2026-06-04
"""

import os
import re
import time
import random
import requests
from bs4 import BeautifulSoup
import pandas as pd

def clean_text(text):
    """텍스트의 양끝 공백을 제거하고 내부의 연속된 공백을 단일 공백으로 치환합니다.

    Args:
        text (str): 공백을 제거하고 정제할 원본 텍스트.

    Returns:
        str: 정제가 완료된 텍스트. 만약 입력값이 없거나 None인 경우 빈 문자열("")을 반환합니다.
    """
    if text:
        return re.sub(r'\s+', ' ', text.strip())
    return ""

def scrape_page(page_number):
    """지정한 페이지 번호의 베스트셀러 데이터를 스크래핑하여 도서 상세 정보 목록으로 반환합니다.

    Args:
        page_number (int): 스크래핑할 대상 페이지 번호.

    Returns:
        list of dict: 각 도서의 메타데이터 및 상세 정보가 담긴 딕셔너리의 리스트.
                      오류가 발생하거나 파싱할 도서가 없는 경우 빈 리스트([])를 반환합니다.
    """
    # YES24 비동기 요청(BestSellerContents) URL 및 매개변수 설정
    url = "https://www.yes24.com/product/category/BestSellerContents"
    params = {
        "categoryNumber": "001001003",  # 카테고리 번호 (소설/시/희곡)
        "sumGb": "06",
        "sex": "A",
        "age": "255",
        "goodsTp": "0",
        "addOptionTp": "0",
        "excludeTp": "2",
        "pageNumber": str(page_number),
        "pageSize": "24",  # 페이지당 도서 수
        "goodsStatGb": "06",
        "eBookTp": "0",
        "bestType": "YES24_BESTSELLER",
        "type": "",
        "saleYear": "0",
        "saleMonth": "0",
        "weekNo": "0",
        "saleDts": "",
        "viewMode": "",
        "freeYn": ""
    }
    
    # 봇 차단을 우회하기 위한 요청 헤더(Header) 정의
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "Referer": f"https://www.yes24.com/product/category/bestseller?categoryNumber=001001003&pageNumber={page_number}&pageSize=24",
        "X-Requested-With": "XMLHttpRequest",
        "Host": "www.yes24.com"
    }
    
    # HTTP GET 요청 수행
    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        print(f"에러: 페이지 {page_number} 호출 시 HTTP {response.status_code} 발생")
        return []
        
    soup = BeautifulSoup(response.text, 'lxml')
    book_lis = soup.select('li')
    
    data_list = []
    for li in book_lis:
        # data-goods-no(도서 고유 식별 번호)가 존재하지 않는 <li>는 건너뜁니다.
        goods_no = li.get('data-goods-no')
        if not goods_no:
            continue
            
        # 1. 도서 순위
        rank_elem = li.select_one('em.ico.rank')
        rank = rank_elem.text.strip() if rank_elem else ""
        
        # 2. 도서 이미지 주소 및 대체 텍스트(제목)
        img_elem = li.select_one('div.item_img img.lazy') or li.select_one('div.item_img img')
        img_link = ""
        alt_text = ""
        if img_elem:
            img_link = img_elem.get('data-original') or img_elem.get('src') or ""
            alt_text = img_elem.get('alt', '')
            
        # 3. 도서 구분 (예: [도서], [eBook])
        gd_res_elem = li.select_one('span.gd_res')
        goods_type = gd_res_elem.text.strip() if gd_res_elem else ""
        
        # 4. 도서명
        gd_name_elem = li.select_one('a.gd_name')
        goods_name = gd_name_elem.text.strip() if gd_name_elem else alt_text
        
        # 5. 상세 페이지 링크
        goods_link = ""
        if gd_name_elem and gd_name_elem.get('href'):
            goods_link = "https://www.yes24.com" + gd_name_elem.get('href')
            
        # 6. 부제목 / 한줄 설명
        gd_name_e_elem = li.select_one('span.gd_nameE')
        goods_subtitle = gd_name_e_elem.text.strip() if gd_name_e_elem else ""
        
        # 7. 저자, 출판사, 출판일 파싱 및 정제
        auth_elem = li.select_one('span.info_auth')
        author = clean_text(auth_elem.text) if auth_elem else ""
        # 저자명 마지막에 붙은 ' 저' 제거
        if author.endswith(' 저'):
            author = author[:-2].strip()
            
        pub_elem = li.select_one('span.info_pub')
        publisher = pub_elem.text.strip() if pub_elem else ""
        
        date_elem = li.select_one('span.info_date')
        publish_date = date_elem.text.strip() if date_elem else ""
        
        # 8. 가격 및 포인트 정보
        # 할인율 (예: 10%)
        sale_elem = li.select_one('span.txt_sale em.num')
        discount_rate = sale_elem.text.strip() if sale_elem else ""
        
        # 판매가 (예: 29,700)
        sale_price_elem = li.select_one('strong.txt_num em.yes_b')
        sale_price = sale_price_elem.text.strip() if sale_price_elem else ""
        
        # 정가 (예: 33,000)
        original_price_elem = li.select_one('span.txt_num.dash em.yes_m')
        original_price = original_price_elem.text.strip() if original_price_elem else ""
        
        # 포인트 적립액
        point_elem = li.select_one('span.yPoint')
        point = clean_text(point_elem.text) if point_elem else ""
        
        # 9. 평가 및 판매지수
        # 판매지수 수치만 추출
        sale_num_elem = li.select_one('span.saleNum')
        sale_index = ""
        if sale_num_elem:
            sale_index = clean_text(sale_num_elem.text)
            sale_index_match = re.search(r'판매지수\s*([\d,]+)', sale_index)
            if sale_index_match:
                sale_index = sale_index_match.group(1).replace(',', '')
                
        # 회원리뷰 건수 (예: 11)
        rv_count_elem = li.select_one('span.rating_rvCount em.txC_blue')
        review_count = rv_count_elem.text.strip() if rv_count_elem else "0"
        
        # 리뷰 평점 총점 (예: 10.0)
        grade_elem = li.select_one('span.rating_grade em.yes_b')
        rating = grade_elem.text.strip() if grade_elem else "0.0"
        
        # 10. 배송 정보
        deli_elem = li.select_one('div.info_deli')
        delivery_info = clean_text(deli_elem.text) if deli_elem else ""
        
        # 11. 분철 서비스 신청 가능 여부 ('Y' 또는 'N')
        spring_elem = li.select_one('div.info_spring')
        spring_service = clean_text(spring_elem.text) if spring_elem else "N"
        if spring_service != "N" and "분철서비스 이용이 가능한 도서입니다" in spring_service:
            spring_service = "Y"
            
        # 12. 도서 태그 정보
        tag_elems = li.select('div.info_tag span.tag a')
        tags = [t.text.strip() for t in tag_elems]
        tags_str = ", ".join(tags)
        
        # 13. 관련상품 정보
        rel_elem = li.select_one('div.info_relG')
        related_goods = clean_text(rel_elem.text) if rel_elem else ""
        
        # 각 도서의 정보를 하나의 딕셔너리로 결합
        book_info = {
            "goods_no": goods_no,
            "rank": rank,
            "goods_type": goods_type,
            "goods_name": goods_name,
            "goods_subtitle": goods_subtitle,
            "goods_link": goods_link,
            "image_link": img_link,
            "author": author,
            "publisher": publisher,
            "publish_date": publish_date,
            "discount_rate": discount_rate,
            "sale_price": sale_price,
            "original_price": original_price,
            "point": point,
            "sale_index": sale_index,
            "review_count": review_count,
            "rating": rating,
            "delivery_info": delivery_info,
            "spring_service": spring_service,
            "tags": tags_str,
            "related_goods": related_goods
        }
        data_list.append(book_info)
        
    return data_list

def scrape_yes24_bestsellers_all():
    """기존 수집한 CSV 데이터를 안전하게 로드하고, 나머지 페이지 데이터를 마지막 페이지까지 수집 및 추가 저장합니다.
    
    작동 알고리즘:
    1. 기존 CSV 파일('yes24/data/yes24_bestsellers.csv') 유무를 검사합니다.
    2. 존재한다면 기존 데이터프레임을 읽어와 도서 번호를 유니크 셋에 등록하고, 다음 페이지(2페이지)부터 시작하도록 설정합니다.
    3. 존재하지 않는다면 빈 데이터프레임 상태로 시작하여 1페이지부터 스크래핑을 수행합니다.
    4. 무한 루프 내에서 각 페이지 스크래핑 시 0.1~0.5초 사이의 랜덤한 대기 시간(time.sleep)을 부여합니다.
    5. 파싱 결과가 비어있거나 수집된 도서 수가 24권 미만일 경우 마지막 페이지로 인지하고 수집을 종료합니다.
    6. 수집된 신규 도서 목록을 기존 데이터프레임과 병합(concat)한 후, 'utf-8-sig' 인코딩을 적용해 다시 CSV로 저장합니다.
    """
    csv_path = "yes24/data/yes24_bestsellers.csv"
    existing_df = None
    existing_goods_nos = set()
    start_page = 1
    
    # 1. 기존 CSV 파일 데이터 로드
    if os.path.exists(csv_path):
        try:
            existing_df = pd.read_csv(csv_path)
            if not existing_df.empty:
                existing_goods_nos = set(existing_df['goods_no'].astype(str).tolist())
                start_page = 2
                print(f"기존 데이터를 찾았습니다. 수집된 도서 수: {len(existing_df)}개. {start_page}페이지부터 추가 수집을 진행합니다.")
        except Exception as e:
            print(f"기존 CSV 로드 중 오류 발생 (새로 수집함): {e}")
            existing_df = None

    all_data = []
    page = start_page
    
    # 2. 마지막 페이지까지 순회하며 데이터 추가 수집
    while True:
        # 서버 과부하 방지를 위한 0.1 ~ 0.5초 사이의 랜덤 대기
        sleep_time = random.uniform(0.1, 0.5)
        print(f"대기 시간: {sleep_time:.3f}초...")
        time.sleep(sleep_time)
        
        print(f"{page}페이지 수집 중...")
        page_data = scrape_page(page)
        
        # 더 이상 수집할 데이터가 없으면 수집 종료
        if not page_data:
            print(f"{page}페이지에 더 이상 도서 데이터가 없습니다. 수집을 종료합니다.")
            break
            
        # 기존 데이터와 비교하여 신규 도서 중복 검사 및 목록 추가
        new_books_count = 0
        for book in page_data:
            if book["goods_no"] not in existing_goods_nos:
                all_data.append(book)
                existing_goods_nos.add(book["goods_no"])
                new_books_count += 1
                
        print(f"{page}페이지에서 새로운 도서 {new_books_count}개 추가 (총 {len(page_data)}개 중)")
        
        # 수집 개수가 24개 미만인 경우 마지막 페이지로 판단
        if len(page_data) < 24:
            print(f"가져온 도서 수가 24개 미만({len(page_data)}개)이므로 마지막 페이지로 간주합니다.")
            break
            
        page += 1
        
    # 3. 수집된 데이터 병합 및 파일 쓰기
    if all_data:
        new_df = pd.DataFrame(all_data)
        if existing_df is not None:
            final_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            final_df = new_df
            
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        final_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"수집 완료: 기존 데이터와 병합하여 총 {len(final_df)}개의 데이터를 {csv_path}에 저장했습니다.")
    else:
        print("새로 추가된 데이터가 없습니다.")

if __name__ == "__main__":
    scrape_yes24_bestsellers_all()
