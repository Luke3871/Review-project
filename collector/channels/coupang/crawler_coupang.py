#//==============================================================================//#
"""
쿠팡 통합 크롤러 (제품 수집 + 리뷰 수집)
- 제품 목록 자동 수집
- 수집된 제품의 모든 리뷰 크롤링
- 제품별 즉시 저장 (다이소 방식)

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
from config_coupang import (
    PRODUCT_NAME_DETAIL,
    PRODUCT_PRICE_SALE_DETAIL,
    PRODUCT_PRICE_ORIGINAL_DETAIL,
    PRODUCT_DISCOUNT_RATE_DETAIL,
)

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
                print(f"💾 저장: {filename} ({len(products)}개)")
                
                all_products.extend(products)
            
            # 다음 조합 전 대기
            time.sleep(5)
    
    print(f"\n제품 수집 완료: 총 {len(all_products)}개")
    return all_products

#//==============================================================================//#
# STEP 2: 리뷰 수집
#//==============================================================================//#
def extract_product_info(driver):
    """제품 상세 페이지에서 제품 정보 추출"""
    product_info = {}
    
    try:
        # 제품명
        try:
            product_name_elem = driver.find_element(By.CSS_SELECTOR, PRODUCT_NAME_DETAIL)
            product_info['product_name'] = product_name_elem.text.strip()
        except:
            product_info['product_name'] = driver.title
        
        # 할인된 가격
        try:
            sale_price_elem = driver.find_element(By.CSS_SELECTOR, PRODUCT_PRICE_SALE_DETAIL)
            product_info['sale_price'] = sale_price_elem.text.strip()
        except:
            product_info['sale_price'] = None
        
        # 원래 가격
        try:
            original_price_elem = driver.find_element(By.CSS_SELECTOR, PRODUCT_PRICE_ORIGINAL_DETAIL)
            product_info['original_price'] = original_price_elem.text.strip()
        except:
            product_info['original_price'] = None
        
        # 할인율
        try:
            discount_elem = driver.find_element(By.CSS_SELECTOR, PRODUCT_DISCOUNT_RATE_DETAIL)
            product_info['discount_rate'] = discount_elem.text.strip()
        except:
            product_info['discount_rate'] = None
        
        return product_info
        
    except Exception as e:
        print(f"제품 정보 추출 오류: {e}")
        return None

def collect_product_reviews(driver, product_info, max_pages=None):
    """개별 제품의 리뷰 수집 (페이지네이션 포함)"""
    from bs4 import BeautifulSoup
    
    all_reviews = []
    page = 1
    
    # 제품 상세 정보 추출
    detailed_info = extract_product_info(driver)
    if detailed_info:
        product_info.update(detailed_info)
    
    while True:
        try:
            print(f"  페이지 {page} 처리 중...", end=" ")
            
            # BeautifulSoup 파싱
            doc = BeautifulSoup(driver.page_source, "html.parser")
            
            # 리뷰 요소 수집
            reviewer_names = [n.text.strip() if n and n.text.strip() else "익명" 
                            for n in doc.find_all("span", class_="sdp-review__article__list__info__user__name")]
            
            review_stars = []
            for elem in doc.find_all(attrs={"data-rating": True}):
                rating = elem.get("data-rating")
                review_stars.append(rating if rating else "0")
            
            review_dates = [d.text.strip() if d and d.text.strip() else "날짜 없음" 
                          for d in doc.find_all(class_='sdp-review__article__list__info__product-info__reg-date')]
            
            review_contents = [r.text.strip() if r and r.text.strip() else None 
                             for r in doc.find_all(class_='sdp-review__article__list__review__content')]
            
            # 리뷰 데이터 구성
            min_length = min(len(reviewer_names), len(review_stars), 
                           len(review_dates), len(review_contents))
            
            page_reviews = 0
            for i in range(min_length):
                if not review_contents[i]:
                    continue
                    
                review_data = {
                    'product_url': product_info['url'],
                    'product_name': product_info.get('product_name', product_info['name']),
                    'sale_price': product_info.get('sale_price', None),
                    'original_price': product_info.get('original_price', None),
                    'discount_rate': product_info.get('discount_rate', None),
                    'category': product_info['category'],
                    'sort_type': product_info['sort_type'],
                    'rank': product_info['rank'],
                    'reviewer_name': reviewer_names[i] if i < len(reviewer_names) else "익명",
                    'rating': review_stars[i] if i < len(review_stars) else "0",
                    'review_date': review_dates[i] if i < len(review_dates) else "날짜 없음",
                    'review_text': review_contents[i],
                }
                all_reviews.append(review_data)
                page_reviews += 1
            
            print(f"{page_reviews}개 리뷰")
            
            # 최대 페이지 제한
            if max_pages and page >= max_pages:
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
        print(f" 저장: {len(all_reviews)}개 리뷰")
    
    return all_reviews

def crawl_all_reviews(products, max_pages_per_product=None):
    """모든 제품의 리뷰 수집"""
    print("\n" + "#"*60)
    print("STEP 2: 리뷰 수집")
    print("#"*60)
    print(f"총 제품 수: {len(products)}개\n")
    
    driver = make_driver()
    
    try:
        for i, product in enumerate(products, 1):
            print(f"\n[{i}/{len(products)}] {product['name'][:50]}...")
            
            try:
                driver.get(product['url'])
                time.sleep(1)
                
                reviews = collect_product_reviews(driver, product, max_pages_per_product)
                print(f" 완료: {len(reviews)}개 리뷰")
                
                time.sleep(randint(1, 2))
                
            except Exception as e:
                print(f" {e}")
                continue
        
        print(f"리뷰 수집 완료!")
        
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
        print(f"\n{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()