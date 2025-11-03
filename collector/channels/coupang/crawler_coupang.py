"""
쿠팡 리뷰 크롤러 - 수정 버전

주요 수정사항:
1. 페이지네이션 인덱스 오류 수정
2. 리뷰 탭 클릭 로직 개선
3. 대기 시간 증가
4. 에러 핸들링 강화
"""

import time
import random
import pandas as pd
import os
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup


# 카테고리 URL
CATEGORY_URLS = {
    'skincare': 'https://www.coupang.com/np/categories/176530?listSize=120&filterType=&rating=0&isPriceRange=false&minPrice=&maxPrice=&component=&sorter=saleCountDesc&brand=&offerCondition=&filter=&fromComponent=N&channel=user&selectedPlpKeepFilter=',
    'makeup': 'https://www.coupang.com/np/categories/176573?listSize=120&filterType=&rating=0&isPriceRange=false&minPrice=&maxPrice=&component=&sorter=saleCountDesc&brand=&offerCondition=&filter=&fromComponent=N&channel=user&selectedPlpKeepFilter='
}


def make_driver():
    """드라이버 생성"""
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    options.add_argument('user-agent=' + random.choice(user_agents))
    
    driver = uc.Chrome(options=options)
    return driver


def collect_product_info(driver):
    """제품 정보 수집"""
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    product_url = driver.current_url
    
    tag = soup.select_one('span.twc-font-bold')
    product_name = tag.text.strip() if tag else ''
    
    tag = soup.select_one('a.brand-info')
    brand = tag.text.strip() if tag else ''
    
    tags = soup.select('ul.breadcrumb li a')
    category = tags[-2].text.strip() if len(tags) >= 2 else ''
    category_use = tags[-1].text.strip() if len(tags) >= 3 else ''
    
    tag = soup.select_one('div.price-amount.final-price-amount')
    price_sale = tag.text.strip() if tag else ''
    
    tag = soup.select_one('div.price-amount.original-price-amount')
    price_origin = tag.text.strip() if tag else ''
    
    return {
        'product_url': product_url,
        'product_name': product_name,
        'brand': brand,
        'category': category,
        'category_use': category_use,
        'product_price_sale': price_sale,
        'product_price_origin': price_origin
    }


def collect_reviews(driver, product_info, product_ranking):
    """리뷰 수집 (본문 없는 리뷰 제외)"""
    all_reviews = []
    page = 1
    empty_count = 0
    
    while True:
        print(f"    페이지 {page} 수집 중...")
        time.sleep(random.uniform(4, 6))
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        articles = soup.select('article.sdp-review__article__list')
        
        if len(articles) == 0:
            print(f"    더 이상 리뷰 없음")
            break
        
        collected_count = 0
        for idx, article in enumerate(articles):
            # 리뷰 본문 먼저 확인
            tag = article.select_one('div.sdp-review__article__list__review__content')
            review_text = tag.text.strip() if tag else ''
            
            # 본문 없으면 스킵
            if not review_text:
                continue
            
            review_id = article.get('data-review-id', '')
            
            tag = article.select_one('span.sdp-review__article__list__info__user__name')
            reviewer_name = tag.text.strip() if tag else ''
            
            tag = article.select_one('div.sdp-review__article__list__info__product-info__star-orange')
            rating = tag.get('data-rating', '') if tag else ''
            
            tag = article.select_one('div.sdp-review__article__list__info__product-info__reg-date')
            review_date = tag.text.strip() if tag else ''
            
            tag = article.select_one('div.sdp-review__article__list__info__product-info__name')
            selected_option = tag.text.strip() if tag else ''
            
            tag = article.select_one('button.twc-inline-flex.twc-items-center')
            helpful_count = tag.text.strip() if tag else ''
            
            # survey 데이터
            survey_data = {}
            survey_container = article.select_one('div.sdp-review__article__list__survey')
            if survey_container:
                rows = survey_container.select('div.sdp-review__article__list__survey__row')
                for row in rows:
                    label = row.select_one('span.sdp-review__article__list__survey__row__question')
                    value = row.select_one('span.sdp-review__article__list__survey__row__answer')
                    if label and value:
                        survey_data[label.text.strip()] = value.text.strip()
            
            review = {
                'review_id': review_id,
                'captured_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'channel': 'Coupang',
                **product_info,
                'sort_type': 'RECENCY',
                'ranking': product_ranking,
                'reviewer_name': reviewer_name,
                'rating': rating,
                'review_date': review_date,
                'selected_option': selected_option,
                'helpful_count': helpful_count,
                'review_text': review_text,
                **survey_data
            }
            
            all_reviews.append(review)
            collected_count += 1
        
        print(f"    {collected_count}개 수집 ({len(articles) - collected_count}개 본문 없음)")
        
        if collected_count == 0:
            empty_count += 1
            if empty_count >= 2:
                print(f"    본문 없는 리뷰만 연속 {empty_count}페이지 - 수집 중단")
                break
        else:
            empty_count = 0
        
        # ===== 수정된 페이지네이션 로직 =====
        try:
            page_in_group = (page - 1) % 10 + 1  # 1~10
            
            if page_in_group == 10:
                # 다음 그룹으로 이동 (11~20페이지로)
                next_arrow = driver.find_element(By.CSS_SELECTOR, 'button.sdp-review__article__page__next.js_reviewArticlePageNextBtn')
                if 'disabled' in next_arrow.get_attribute('class'):
                    print(f"    마지막 페이지")
                    break
                
                driver.execute_script("arguments[0].click();", next_arrow)
                time.sleep(random.uniform(5, 7))
            else:
                # 같은 그룹 내에서 페이지 이동
                page_buttons = driver.find_elements(By.CSS_SELECTOR, 'button.sdp-review__article__page__num')
                
                # ✅ 수정: page_in_group이 2면 인덱스 1을 클릭해야 함
                button_index = page_in_group  # 2페이지 = 인덱스 1
                
                if button_index < len(page_buttons):
                    driver.execute_script("arguments[0].click();", page_buttons[button_index])
                    time.sleep(random.uniform(5, 7))
                else:
                    print(f"    페이지 버튼 없음 (인덱스: {button_index}, 총 버튼: {len(page_buttons)})")
                    break
            
            page += 1
            
        except Exception as e:
            print(f"    페이지 이동 실패: {e}")
            break
    
    return all_reviews


def save_to_csv(reviews, product_info, product_ranking):
    """CSV 저장"""
    if not reviews:
        print("  수집된 리뷰 없음")
        return
    
    df = pd.DataFrame(reviews)
    
    save_dir = "data/coupang_reviews"
    os.makedirs(save_dir, exist_ok=True)
    
    category_safe = product_info['category'].replace('/', '_').replace('\\', '_')
    product_name_safe = product_info['product_name'].replace('/', '_').replace('\\', '_').replace(':', '_')[:50]
    filename = f"{category_safe}_RECENCY_rank{product_ranking:03d}_{product_name_safe}.csv"
    filepath = os.path.join(save_dir, filename)
    
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    print(f"  저장: {filename} ({len(reviews)}개 리뷰)")


def get_collected_rankings(save_dir, category_name):
    """이미 수집된 랭킹 번호 확인"""
    collected = set()
    if os.path.exists(save_dir):
        for filename in os.listdir(save_dir):
            if filename.startswith(category_name) and filename.endswith('.csv'):
                try:
                    rank_str = filename.split('_rank')[1].split('_')[0]
                    collected.add(int(rank_str))
                except:
                    continue
    return collected


def crawl_category(driver, category_name, category_url, max_products=100, start_from=1):
    """카테고리별 크롤링"""
    print("\n" + "="*60)
    print(f"{category_name} 크롤링 시작 (랭킹 {start_from}번부터)")
    print("="*60)
    
    save_dir = "data/coupang_reviews"
    collected_rankings = get_collected_rankings(save_dir, category_name)
    print(f"이미 수집된 제품: {len(collected_rankings)}개")
    
    driver.get(category_url)
    time.sleep(6)  # ✅ 대기 시간 증가
    
    main_window = driver.current_window_handle
    
    selector = '.ProductUnit_productUnit__Qd6sv a'
    links = driver.find_elements(By.CSS_SELECTOR, selector)
    print(f"발견된 제품: {len(links)}개")
    
    total_products = min(max_products, len(links))
    
    for i in range(start_from - 1, total_products):
        product_ranking = i + 1
        
        if product_ranking in collected_rankings:
            print(f"\n[{product_ranking}/{total_products}] 이미 수집됨 - 건너뛰기")
            continue
        
        print(f"\n[{product_ranking}/{total_products}] 제품 크롤링 중...")
        
        try:
            # 제품 링크 다시 찾기
            links = driver.find_elements(By.CSS_SELECTOR, selector)
            
            # 현재 윈도우 핸들 저장
            original_handles = driver.window_handles
            print(f"  현재 윈도우 수: {len(original_handles)}")
            
            # 새 탭 열기
            actions = ActionChains(driver)
            actions.key_down(Keys.CONTROL).click(links[i]).key_up(Keys.CONTROL).perform()
            
            # 새 탭이 열릴 때까지 대기 (최대 10초)
            max_wait = 10
            for wait_time in range(max_wait):
                time.sleep(1)
                current_handles = driver.window_handles
                if len(current_handles) > len(original_handles):
                    print(f"  새 탭 감지됨 ({wait_time+1}초)")
                    break
            
            # 새 윈도우 핸들 찾기
            new_handles = [h for h in driver.window_handles if h not in original_handles]
            if not new_handles:
                print(f"  새 탭이 열리지 않음 - 건너뛰기")
                continue
            
            # 새 탭으로 전환
            driver.switch_to.window(new_handles[0])
            print(f"  새 탭으로 전환 완료")
            time.sleep(4)
            
            # 제품 정보 수집
            product_info = collect_product_info(driver)
            print(f"  제품: {product_info['product_name'][:50]}")
            
            # ===== 수정된 리뷰 탭 클릭 로직 =====
            try:
                # 여러 방법으로 시도
                review_clicked = False
                
                # 방법 1: XPath로 "상품평" 텍스트
                try:
                    review_tab = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '상품평')]"))
                    )
                    driver.execute_script("arguments[0].click();", review_tab)
                    review_clicked = True
                    print("  리뷰 탭 클릭 성공 (방법 1)")
                except:
                    pass
                
                # 방법 2: CSS Selector
                if not review_clicked:
                    try:
                        review_tab = driver.find_element(By.CSS_SELECTOR, "a[href*='#sdp-review']")
                        driver.execute_script("arguments[0].click();", review_tab)
                        review_clicked = True
                        print("  리뷰 탭 클릭 성공 (방법 2)")
                    except:
                        pass
                
                if not review_clicked:
                    raise Exception("리뷰 탭을 찾을 수 없음")
                
                time.sleep(8)
                
                # 리뷰 로딩 대기
                for attempt in range(5):  # ✅ 시도 횟수 증가
                    soup_check = BeautifulSoup(driver.page_source, 'html.parser')
                    articles_check = soup_check.select('article.sdp-review__article__list')
                    if len(articles_check) > 0:
                        print(f"  리뷰 로딩 완료 ({len(articles_check)}개)")
                        break
                    print(f"  리뷰 로딩 대기 중... ({attempt+1}/5)")
                    time.sleep(3)
                
            except Exception as e:
                print(f"  리뷰 탭 클릭 실패: {e}")
                driver.close()
                driver.switch_to.window(main_window)
                continue
            
            # 리뷰 수집
            reviews = collect_reviews(driver, product_info, product_ranking)
            
            # CSV 저장
            save_to_csv(reviews, product_info, product_ranking)
            
            # 탭 닫기
            driver.close()
            driver.switch_to.window(main_window)
            
            # 3개마다 5분 대기
            if product_ranking % 3 == 0 and product_ranking < total_products:
                print(f"\n3개 수집 완료 - 5분 대기 중...")
                time.sleep(300)
            else:
                time.sleep(random.uniform(4, 6))  # ✅ 대기 시간 증가
            
        except Exception as e:
            print(f"  오류: {e}")
            import traceback
            traceback.print_exc()  # ✅ 상세 에러 출력
            
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(main_window)
            continue
    
    print(f"\n{category_name} 크롤링 완료")


def main():
    """메인 함수"""
    print("="*60)
    print("쿠팡 리뷰 크롤러 시작")
    print("="*60)
    print("메이크업 100개")
    print("제품 3개마다 5분 대기")
    print("="*60)
    
    driver = make_driver()
    
    try:
        # 메이크업만 실행
        crawl_category(driver, "스킨케어", CATEGORY_URLS['skincare'], max_products=100, start_from=85)
        
        print("\n" + "="*60)
        print("크롤링 완료!")
        print("="*60)
        
    finally:
        driver.quit()


if __name__ == "__main__":
    main()