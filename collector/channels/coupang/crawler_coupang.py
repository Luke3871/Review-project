#//==============================================================================//#
"""
쿠팡 TOP 100 제품 리뷰 크롤러 (최종 버전)
- 4개 카테고리 조합의 모든 제품 리뷰 수집
- 제품별 페이지네이션 처리 (모든 페이지)
- 다이소 방식 적용: 제품별 즉시 저장

last_updated : 2025.09.10
"""
#//==============================================================================//#

import time
import pandas as pd
import os
import glob
from selenium.webdriver.common.by import By
from random import randint
from driver_coupang import make_driver
from navigator_coupang import go_to_page
from config_coupang import (
    PRODUCT_NAME_DETAIL,
    PRODUCT_PRICE_SALE_DETAIL,
    PRODUCT_PRICE_ORIGINAL_DETAIL,
    PRODUCT_DISCOUNT_RATE_DETAIL,
    REVIEW_CONTAINER,
    REVIEW_ITEM,
    REVIEWER_NAME,
    REVIEW_RATING,
    REVIEW_DATE,
    REVIEW_TEXT
)

#//==============================================================================//#
# 제품 정보 추출
#//==============================================================================//#
def extract_product_info(driver):
    """제품 상세 페이지에서 제품 정보 추출"""
    product_info = {}
    
    try:
        # 제품명
        try:
            product_name_elem = driver.find_element(By.CSS_SELECTOR, PRODUCT_NAME_DETAIL)
            product_name = product_name_elem.text.strip()
            product_info['product_name'] = product_name
        except:
            product_info['product_name'] = driver.title
        
        # 할인된 가격
        try:
            sale_price_elem = driver.find_element(By.CSS_SELECTOR, PRODUCT_PRICE_SALE_DETAIL)
            sale_price = sale_price_elem.text.strip()
            product_info['sale_price'] = sale_price
        except:
            product_info['sale_price'] = None
        
        # 원래 가격
        try:
            original_price_elem = driver.find_element(By.CSS_SELECTOR, PRODUCT_PRICE_ORIGINAL_DETAIL)
            original_price = original_price_elem.text.strip()
            product_info['original_price'] = original_price
        except:
            product_info['original_price'] = None
        
        # 할인율
        try:
            discount_elem = driver.find_element(By.CSS_SELECTOR, PRODUCT_DISCOUNT_RATE_DETAIL)
            discount_rate = discount_elem.text.strip()
            product_info['discount_rate'] = discount_rate
        except:
            product_info['discount_rate'] = None
        
        return product_info
        
    except Exception as e:
        print(f"제품 정보 추출 오류: {e}")
        return None

#//==============================================================================//#
# 페이지네이션 포함 리뷰 수집 (검증된 방식)
#//==============================================================================//#
def collect_product_reviews(driver, product_info, max_pages=None):
    """
    개별 제품 페이지에서 리뷰 수집 (페이지네이션 포함)
    검증된 BeautifulSoup 방식 + 페이지네이션
    
    Args:
        driver: Selenium WebDriver
        product_info: 제품 정보 딕셔너리
        max_pages: 최대 수집 페이지 수 (None이면 모든 페이지)
        
    Returns:
        List[Dict]: 수집된 리뷰 리스트
    """
    from bs4 import BeautifulSoup
    
    all_reviews = []
    page = 1
    
    # 제품 상세 정보 추출 (한 번만)
    detailed_info = extract_product_info(driver)
    if detailed_info:
        product_info.update(detailed_info)
    
    while True:
        try:
            print(f"페이지 {page} 처리 중...")
            
            # 현재 페이지 파싱 (BeautifulSoup 방식)
            doc = BeautifulSoup(driver.page_source, "html.parser")
            
            # 개별 리뷰 요소들 수집 (쿠팡 셀렉터 적용)
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
            
            # 리뷰 개수 맞추기 (가장 짧은 리스트 길이 기준)
            min_length = min(len(reviewer_names), len(review_stars), 
                           len(review_dates), len(review_contents))
            
            if min_length == 0:
                print(f"페이지 {page}: 리뷰 없음")
            else:
                # 리뷰 데이터 구성
                page_reviews = 0
                for i in range(min_length):
                    # 리뷰 내용이 없으면 스킵
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
                
                print(f"페이지 {page}: {page_reviews}개 리뷰 수집")
            
            # 최대 페이지 제한 확인
            if max_pages and page >= max_pages:
                print(f"최대 페이지({max_pages}) 도달")
                break
            
            # 다음 페이지로 이동
            next_page = page + 1
            if not go_to_page(driver, next_page):
                print("마지막 페이지에 도달했습니다.")
                break
            
            page += 1
            time.sleep(randint(1, 3))
                
        except Exception as e:
            print(f"페이지 {page} 처리 중 오류: {e}")
            break
    
    # 리뷰 수집 완료 후 즉시 저장 (다이소 방식)
    if all_reviews:
        reviews_dir = os.path.join("src", "channels", "coupang", "data_coupang", "reviews_coupang")
        os.makedirs(reviews_dir, exist_ok=True)
        
        # 제품별 파일명 생성
        safe_name = product_info['name'].replace('/', '_').replace('\\', '_')[:50]
        filename = f"{product_info['category']}_{product_info['sort_type']}_{safe_name}_reviews.csv"
        filepath = os.path.join(reviews_dir, filename)
        
        # CSV 저장
        reviews_df = pd.DataFrame(all_reviews)
        reviews_df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"저장 완료: {filepath} ({len(all_reviews)}개 리뷰)")
    
    return all_reviews

#//==============================================================================//#
# 전체 리뷰 크롤링 (다이소 방식)
#//==============================================================================//#
def crawl_coupang_reviews(max_pages_per_product=None):
    """
    수집된 제품 URL로부터 리뷰 데이터 크롤링
    다이소 방식 적용
    """
    print("\n=== 쿠팡 리뷰 크롤링 시작 ===")
    
    # CSV 파일들 읽어오기
    products_dir = os.path.join("src", "channels", "coupang", "data_coupang", "products_coupang")
    csv_files = glob.glob(os.path.join(products_dir, "coupang_*.csv"))
    
    if not csv_files:
        print("제품 CSV 파일을 찾을 수 없습니다.")
        return False
    
    print(f"발견된 CSV 파일: {len(csv_files)}개")
    for csv_file in csv_files:
        print(f"  - {os.path.basename(csv_file)}")
    
    # 모든 제품 URL 수집
    all_products = []
    for csv_file in csv_files:
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
        for _, row in df.iterrows():
            all_products.append({
                'url': row['url'],
                'name': row['name'],
                'category': row['category'],
                'sort_type': row['sort_type'],
                'rank': row.get('rank', 0)
            })
    
    print(f"총 제품 수: {len(all_products)}개")
    
    # 리뷰 수집 시작
    driver = make_driver()
    
    try:
        for i, product in enumerate(all_products, 1):
            print(f"\n[{i}/{len(all_products)}] {product['name'][:50]}... 리뷰 수집 중...")
            
            try:
                # 제품 페이지로 이동
                driver.get(product['url'])
                time.sleep(5)
                
                # 리뷰 데이터 수집
                reviews = collect_product_reviews(driver, product, max_pages_per_product)
                
                print(f"제품 {i} 완료: {len(reviews)}개 리뷰")
                
                # 요청 간격 조절 (봇 감지 방지)
                time.sleep(randint(2, 5))
                
            except Exception as e:
                print(f"제품 {i} 리뷰 수집 실패: {e}")
                continue
        
        print(f"\n리뷰 크롤링 완료!")
        print(f"총 처리된 제품: {len(all_products)}개")
        return True
        
    except Exception as e:
        print(f"리뷰 크롤링 중 오류: {e}")
        return False
    
    finally:
        driver.quit()

#//==============================================================================//#
# 메인 실행
#//==============================================================================//#
def main():
    """메인 함수 - 모든 페이지 리뷰 수집"""
    print("쿠팡 TOP 100 제품 리뷰 크롤러")
    print("=" * 50)
    
    # 모든 페이지 리뷰 수집 (max_pages=None)
    success = crawl_coupang_reviews(max_pages_per_product=None)
    
    if success:
        print("\n모든 작업이 완료되었습니다!")
    else:
        print("\n작업 중 오류가 발생했습니다.")

if __name__ == "__main__":
    main()