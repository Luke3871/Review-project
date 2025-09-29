#//==============================================================================//#
"""
쿠팡 통합 크롤러 (제품 수집 + 리뷰 수집)
- 제품 목록 자동 수집
- 수집된 제품의 모든 리뷰 크롤링
- 제품별 즉시 저장 (다이소 방식)
- 표준 컬럼명 사용 (RAG 준비)

last_updated : 2025.09.29
"""
#//==============================================================================//#

import time
import pandas as pd
import os
from datetime import datetime
from selenium.webdriver.common.by import By
from random import randint
from driver_coupang import make_driver
from navigator_coupang import navigate_to_category, collect_product_cards, go_to_page
from parser_coupang import parse_product_card

#//==============================================================================//#
# STEP 1: 제품 목록 수집
#//==============================================================================//#
def collect_products(category, sort_type, max_products=100):
    """특정 카테고리/정렬 조건의 제품 목록 수집"""
    print(f"\n{'='*60}")
    print(f"제품 수집 | 카테고리: {category} | 정렬: {sort_type}")
    print(f"{'='*60}")
    
    driver = make_driver()
    products = []
    
    try:
        # 카테고리 페이지 이동
        if not navigate_to_category(driver, category, sort_type, list_size=120):
            print("페이지 이동 실패")
            return products
        
        # 제품 카드 수집
        product_cards = collect_product_cards(driver, max_products=max_products)
        
        if not product_cards:
            print("제품 카드를 찾을 수 없습니다.")
            return products
        
        # 각 제품 카드 파싱
        for rank, card in enumerate(product_cards, 1):
            product_data = parse_product_card(card, rank, category, sort_type)
            
            if product_data:
                products.append(product_data)
                print(f"[{rank}] {product_data['name'][:40]}...")
            
            time.sleep(randint(1, 2))
        
        print(f"\n수집 완료: {len(products)}개 제품")
        
    except Exception as e:
        print(f"수집 중 오류: {e}")
    
    finally:
        driver.quit()
    
    return products

def collect_all_products():
    """모든 카테고리/정렬 조합의 제품 목록 수집"""
    print("\n" + "#"*60)
    print("STEP 1: 제품 목록 수집")
    print("#"*60)
    
    categories = ['skincare', 'makeup']
    sort_types = ['SALES', 'RANKED_COUPANG']
    
    save_dir = os.path.join("data", "data_coupang", "raw_data", "products_coupang")
    os.makedirs(save_dir, exist_ok=True)
    
    all_products = []
    
    for category in categories:
        for sort_type in sort_types:
            products = collect_products(category, sort_type, max_products=100)
            
            if products:
                # DataFrame 변환 및 저장
                df = pd.DataFrame(products)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"coupang_{category}_{sort_type}_{timestamp}.csv"
                filepath = os.path.join(save_dir, filename)
                
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
                print(f"저장: {filename} ({len(products)}개)")
                
                all_products.extend(products)
            
            # 다음 조합 전 대기
            time.sleep(5)
    
    print(f"\n제품 수집 완료: 총 {len(all_products)}개")
    return all_products

#//==============================================================================//#
# STEP 2: 리뷰 수집
#//==============================================================================//#
def collect_product_reviews(driver, product_info, max_pages_per_product, collection_date):
    """개별 제품의 리뷰 수집 (페이지네이션 포함)"""
    from bs4 import BeautifulSoup
    
    all_reviews = []
    page = 1
    
    # 제품 상세 페이지에서 추가 정보 추출 (최초 1회만)
    brand_name = ""
    category_use = ""
    
    try:
        doc_initial = BeautifulSoup(driver.page_source, "html.parser")
        
        # 브랜드명 추출
        brand_elem = doc_initial.find("div", class_="twc-text-sm twc-text-blue-600")
        if brand_elem:
            brand_name = brand_elem.text.strip()
        
        # 세부 카테고리 추출 (breadcrumb 마지막 항목)
        breadcrumb_items = doc_initial.select("ul li a")
        if breadcrumb_items and len(breadcrumb_items) > 0:
            category_use = breadcrumb_items[-1].text.strip()
    except:
        pass
    
    while True:
        try:
            print(f"  페이지 {page} 처리 중...", end=" ")
            time.sleep(3)
            # BeautifulSoup 파싱
            doc = BeautifulSoup(driver.page_source, "html.parser")
            
            # 리뷰 컨테이너 찾기 (개별 리뷰를 각각 파싱)
            review_containers = doc.find_all("article", class_="sdp-review__article__list")
            
            if not review_containers:
                print("리뷰 없음")
                break
            
            page_reviews = 0
            for idx, container in enumerate(review_containers, 1):
                try:
                    # 리뷰어 이름
                    reviewer_name_elem = container.find("span", class_="sdp-review__article__list__info__user__name")
                    reviewer_name = reviewer_name_elem.text.strip() if reviewer_name_elem else "익명"
                    
                    # 평점
                    rating_elem = container.find(attrs={"data-rating": True})
                    rating = rating_elem.get("data-rating") if rating_elem else "0"
                    
                    # 리뷰 날짜
                    date_elem = container.find(class_='sdp-review__article__list__info__product-info__reg-date')
                    review_date = date_elem.text.strip() if date_elem else ""
                    
                    # 리뷰 내용
                    content_elem = container.find(class_='sdp-review__article__list__review__content')
                    review_text = content_elem.text.strip() if content_elem else None
                    
                    if not review_text:
                        continue
                    
                    # 도움이 됨 카운트
                    helpful_count = ""
                    try:
                        helpful_div = container.find("div", class_="sdp-review__article__list__help_count")
                        if helpful_div:
                            helpful_strong = helpful_div.find("strong")
                            if helpful_strong:
                                helpful_count = helpful_strong.text.strip()
                    except:
                        pass
                    
                    # 선택 옵션 (구매 옵션)
                    selected_option = ""
                    try:
                        option_elem = container.find("div", class_="sdp-review__article__list__info__product-info__name")
                        if option_elem:
                            selected_option = option_elem.text.strip()
                    except:
                        pass
                    
                    # 평가 항목 수집 (향 만족도, 보습력 등)
                    survey_data = {}
                    try:
                        survey_rows = container.find_all("div", class_="sdp-review__article__list__survey_row")
                        for row in survey_rows:
                            question_elem = row.find("span", class_="sdp-review__article__list__survey_row__question")
                            answer_elem = row.find("span", class_="sdp-review__article__list__survey_row__answer")
                            
                            if question_elem and answer_elem:
                                question = question_elem.text.strip()
                                answer = answer_elem.text.strip()
                                survey_data[question] = answer
                    except:
                        pass
                    
                    # review_id 생성 (coupang_제품순위_페이지_리뷰순번)
                    review_id = f"coupang_{product_info['rank']:03d}_{page:03d}_{idx:03d}"
                    
                    # 리뷰 데이터 구성 (표준 컬럼명 사용)
                    review_data = {
                        'review_id': review_id,
                        'captured_at': collection_date,
                        'channel': 'Coupang',
                        'product_url': product_info['url'],
                        'product_name': product_info['name'],
                        'brand': brand_name,
                        'category': product_info['category'],
                        'category_use': category_use,
                        'product_price_sale': product_info.get('sale_price', ''),
                        'product_price_origin': product_info.get('original_price', ''),
                        'sort_type': product_info['sort_type'],
                        'ranking': product_info['rank'],
                        'reviewer_name': reviewer_name,
                        'rating': rating,
                        'review_date': review_date,
                        'selected_option': selected_option,
                        'review_text': review_text,
                        'helpful_count': helpful_count,
                        **survey_data
                    }
                    
                    all_reviews.append(review_data)
                    page_reviews += 1
                    
                except Exception as e:
                    continue
            
            print(f"{page_reviews}개 리뷰")
            
            # 최대 페이지 제한
            if max_pages_per_product and page >= max_pages_per_product:
                break
            
            # 다음 페이지 이동
            next_page = page + 1
            if not go_to_page(driver, next_page):
                break
            
            page += 1
            time.sleep(randint(1, 2))
                
        except Exception as e:
            print(f"오류: {e}")
            break
    
    # 제품별 즉시 저장
    if all_reviews:
        reviews_dir = os.path.join("data", "data_coupang", "raw_data", "reviews_coupang")
        os.makedirs(reviews_dir, exist_ok=True)
        
        safe_name = product_info['name'].replace('/', '_').replace('\\', '_')[:50]
        filename = f"{product_info['category']}_{product_info['sort_type']}_rank{product_info['rank']:03d}_{safe_name}.csv"
        filepath = os.path.join(reviews_dir, filename)
        
        reviews_df = pd.DataFrame(all_reviews)
        reviews_df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"  저장: {len(all_reviews)}개 리뷰")
    
    return all_reviews

def crawl_all_reviews(products, max_pages_per_product=None):
    """모든 제품의 리뷰 수집"""
    print("\n" + "#"*60)
    print("STEP 2: 리뷰 수집")
    print("#"*60)
    print(f"총 제품 수: {len(products)}개\n")
    
    # 수집 시작 시간 기록
    collection_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"수집 시작 시간: {collection_date}\n")
    
    driver = make_driver()
    
    try:
        for i, product in enumerate(products, 1):
            print(f"\n[{i}/{len(products)}] {product['name'][:50]}...")
            
            try:
                driver.get(product['url'])
                time.sleep(5)
                
                reviews = collect_product_reviews(driver, product, max_pages_per_product, collection_date)
                print(f"  완료: {len(reviews)}개 리뷰")
                
                time.sleep(randint(2, 4))
                
            except Exception as e:
                print(f"  오류: {e}")
                continue
        
        print(f"\n리뷰 수집 완료!")
        
    except Exception as e:
        print(f"리뷰 수집 중 오류: {e}")
    
    finally:
        driver.quit()

#//==============================================================================//#
# 메인 실행
#//==============================================================================//#
def main():
    """통합 실행: 제품 수집 → 리뷰 수집"""
    print("\n" + "="*60)
    print("쿠팡 통합 크롤러 시작")
    print("="*60)
    
    try:
        # STEP 1: 제품 목록 수집
        products = collect_all_products()
        
        if not products:
            print("제품 수집 실패")
            return
        
        # STEP 2: 리뷰 수집
        crawl_all_reviews(products, max_pages_per_product=None)
        
        print("\n" + "="*60)
        print("모든 작업 완료!")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()