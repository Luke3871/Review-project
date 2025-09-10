#//==============================================================================//#
"""
쿠팡 리뷰 크롤러 실행 테스트 (기존 함수 활용)
- 이미 만든 함수들 재사용
- 소수 제품으로 전체 로직 확인

last_updated : 2025.09.10
"""
#//==============================================================================//#

import time
import pandas as pd
import os
import glob
from random import randint
from driver_coupang import make_driver
from navigator_coupang import go_to_page

# 기존에 만든 함수들 import
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
# 기존 함수들 복사 (테스트용)
#//==============================================================================//#
def extract_product_info(driver):
    """제품 상세 페이지에서 제품 정보 추출"""
    from selenium.webdriver.common.by import By
    
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

def collect_product_reviews_test(driver, product_info, max_pages=3):
    """
    기존 BeautifulSoup 방식 + 페이지네이션 테스트
    """
    from bs4 import BeautifulSoup
    
    all_reviews = []
    page = 1
    
    # 제품 상세 정보 추출 (한 번만)
    detailed_info = extract_product_info(driver)
    if detailed_info:
        product_info.update(detailed_info)
        print(f"제품 정보 업데이트: {detailed_info}")
    
    while page <= max_pages:
        try:
            print(f"\n페이지 {page} 처리 중...")
            
            # 현재 페이지 파싱 (BeautifulSoup 방식)
            doc = BeautifulSoup(driver.page_source, "html.parser")
            
            # 리뷰 컨테이너 확인
            containers = doc.find_all(class_='js_reviewArticleListContainer')
            print(f"리뷰 컨테이너: {len(containers)}개")
            
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
            
            print(f"찾은 요소들:")
            print(f"- 리뷰어 이름: {len(reviewer_names)}개")
            print(f"- 평점: {len(review_stars)}개") 
            print(f"- 날짜: {len(review_dates)}개")
            print(f"- 내용: {len(review_contents)}개")
            
            # 리뷰 개수 맞추기 (가장 짧은 리스트 길이 기준)
            min_length = min(len(reviewer_names), len(review_stars), 
                           len(review_dates), len(review_contents))
            
            print(f"실제 처리할 리뷰 수: {min_length}개")
            
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
                
                print(f"페이지 {page}: {page_reviews}개 리뷰 수집 완료")
            
            # 다음 페이지로 이동
            if page < max_pages:
                next_page = page + 1
                print(f"페이지 {next_page}로 이동 시도...")
                if go_to_page(driver, next_page):
                    page += 1
                    time.sleep(3)  # 페이지 로드 대기 시간 증가
                else:
                    print("페이지 이동 실패 - 크롤링 종료")
                    break
            else:
                break
                
        except Exception as e:
            print(f"페이지 {page} 처리 중 오류: {e}")
            import traceback
            traceback.print_exc()
            break
    
    print(f"총 수집된 리뷰: {len(all_reviews)}개")
    return all_reviews

#//==============================================================================//#
# 테스트 실행
#//==============================================================================//#
def test_existing_functions():
    """기존 함수들을 활용한 테스트"""
    print("=== 기존 함수 활용 테스트 시작 ===")
    
    # CSV 파일 확인
    products_dir = os.path.join("src", "channels", "coupang", "data_coupang", "products_coupang")
    csv_files = glob.glob(os.path.join(products_dir, "coupang_*.csv"))
    
    if not csv_files:
        print("제품 CSV 파일을 찾을 수 없습니다.")
        return
    
    print(f"CSV 파일 발견: {csv_files[0]}")
    
    # 첫 번째 CSV에서 1개 제품만 테스트
    df = pd.read_csv(csv_files[0], encoding='utf-8-sig')
    test_product = df.iloc[0].to_dict()
    
    print(f"테스트 제품: {test_product['name']}")
    
    driver = make_driver()
    
    try:
        # 제품 페이지 접속
        print(f"\n제품 페이지 접속: {test_product['url']}")
        driver.get(test_product['url'])
        time.sleep(5)
        
        # 기존 함수를 활용한 리뷰 수집 (3페이지)
        reviews = collect_product_reviews_test(driver, test_product, max_pages=3)
        
        if reviews:
            print(f"\n수집 성공: {len(reviews)}개 리뷰")
            
            # 결과 저장
            test_dir = os.path.join("src", "channels", "coupang", "data_coupang", "reviews_coupang")
            os.makedirs(test_dir, exist_ok=True)
            
            df_reviews = pd.DataFrame(reviews)
            test_file = os.path.join(test_dir, "test_existing_functions_reviews.csv")
            df_reviews.to_csv(test_file, index=False, encoding='utf-8-sig')
            
            print(f"테스트 파일 저장: {test_file}")
            
            # 샘플 데이터 출력
            print(f"\n샘플 리뷰:")
            for i, review in enumerate(reviews[:3]):
                print(f"{i+1}. {review['reviewer_name']} | {review['rating']}점 | {review['review_text'][:50]}...")
        else:
            print("리뷰 수집 실패")
        
    except Exception as e:
        print(f"테스트 오류: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()

if __name__ == "__main__":
    test_existing_functions()