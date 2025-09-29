#//==============================================================================//#
"""
올리브영 크롤러 - 완성 버전

기능:
- 스킨케어/메이크업 랭킹 TOP 100 제품 수집
- 각 제품별 모든 페이지 리뷰 데이터 크롤링
- 제품별 개별 CSV 파일 저장

last_updated : 2025.09.26
"""
#//==============================================================================//#

import undetected_chromedriver as uc
import time
import pandas as pd
import os
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 카테고리 URL
SKINCARE_URL = "https://www.oliveyoung.co.kr/store/main/getBestList.do?dispCatNo=900000100100001&fltDispCatNo=10000010001&pageIdx=1&rowsPerPage=8&t_page=랭킹&t_click=판매랭킹_스킨케어"
MAKEUP_URL = "https://www.oliveyoung.co.kr/store/main/getBestList.do?dispCatNo=900000100100001&fltDispCatNo=10000010002&pageIdx=1&rowsPerPage=8&t_page=랭킹&t_click=판매랭킹_메이크업"

# 저장 경로
SAVE_PATH = r"C:\Users\lluke\OneDrive\바탕 화면\ReviewFW_LG_hnh\data\data_oliveyoung\raw_data\reviews_oliveyoung"

def collect_product_reviews(driver, product_name, ranking, category_name, max_reviews_per_batch=1000):
    """개별 제품의 모든 페이지 리뷰 수집 (배치 처리)"""
    all_product_reviews = []
    batch_num = 1
    
    while True:
        print(f"\n--- 배치 {batch_num} 시작 (최대 {max_reviews_per_batch}개) ---")
        batch_reviews = []
        page_num = 1
        
        while len(batch_reviews) < max_reviews_per_batch:
            print(f"페이지 {page_num} 수집 중...")
            
            # 페이지 이동 (1페이지는 이미 로딩된 상태)
            if page_num > 1:
                try:
                    # 페이지 번호로 클릭 시도
                    page_link = driver.find_element(By.CSS_SELECTOR, f"a[data-page-no='{page_num}']")
                    page_link.click()
                    time.sleep(2)
                except:
                    # 페이지 번호가 없으면 다음 버튼 시도
                    try:
                        next_btn = driver.find_element(By.CSS_SELECTOR, "a.next")
                        if "disabled" in next_btn.get_attribute("class") or not next_btn.is_enabled():
                            print("마지막 페이지 도달")
                            break
                        next_btn.click()
                        time.sleep(2)
                    except:
                        print("더 이상 페이지 없음")
                        break
            
            # 리뷰 데이터 수집
            try:
                # 제품 정보 수집
                try:
                    product_price_before = driver.find_element(By.CSS_SELECTOR, "span.price-1").text.strip()
                except:
                    product_price_before = ""
                
                try:
                    product_price_after = driver.find_element(By.CSS_SELECTOR, "span.price-2").text.strip()
                except:
                    product_price_after = ""
                
                # 평가 항목들 수집
                evaluation_data = {}
                try:
                    eval_items = [ei.text.strip() for ei in driver.find_elements(By.CSS_SELECTOR, "dl.poll_type1 dt span") if ei.text.strip()]
                    eval_values = [ev.text.strip() for ev in driver.find_elements(By.CSS_SELECTOR, "dl.poll_type1 dd span.txt") if ev.text.strip()]
                    evaluation_data = dict(zip(eval_items, eval_values))
                except:
                    pass
                
                # 개별 리뷰 컨테이너들 찾기
                review_containers = driver.find_elements(By.CSS_SELECTOR, "ul.inner_list li")
                
                if not review_containers:
                    print("리뷰가 없는 페이지")
                    break
                
                page_review_count = 0
                for container in review_containers:
                    if len(batch_reviews) >= max_reviews_per_batch:
                        break
                        
                    try:
                        reviewer_name = container.find_element(By.CSS_SELECTOR, "a.id").text.strip()
                        
                        try:
                            reviewer_rank = container.find_element(By.CSS_SELECTOR, "a.top").text.strip()
                        except:
                            reviewer_rank = ""
                        
                        try:
                            skin_features = [sf.text.strip() for sf in container.find_elements(By.CSS_SELECTOR, "p.tag span") if sf.text.strip()]
                            reviewer_skin_text = ",".join(skin_features)
                        except:
                            reviewer_skin_text = ""
                        
                        rating = container.find_element(By.CSS_SELECTOR, "span.point").text.strip()
                        review_date = container.find_element(By.CSS_SELECTOR, "span.date").text.strip()
                        
                        try:
                            selected_option = container.find_element(By.CSS_SELECTOR, "p.item_option").text.strip()
                        except:
                            selected_option = ""
                        
                        review_content = container.find_element(By.CSS_SELECTOR, "div.txt_inner").text.strip()
                        
                        try:
                            helpful_count = container.find_element(By.CSS_SELECTOR, "div.recom_area span").text.strip()
                        except:
                            helpful_count = ""
                        
                        review_data = {
                            'category': category_name,
                            'ranking': ranking,
                            'product_name': product_name,
                            'product_price_before': product_price_before,
                            'product_price_after': product_price_after,
                            'reviewer_name': reviewer_name,
                            'reviewer_rank': reviewer_rank,
                            'reviewer_skin_features': reviewer_skin_text,
                            'rating': rating,
                            'review_date': review_date,
                            'selected_option': selected_option,
                            'review_content': review_content,
                            'helpful_count': helpful_count,
                            **evaluation_data
                        }
                        batch_reviews.append(review_data)
                        page_review_count += 1
                        
                    except Exception as e:
                        continue
                
                print(f"페이지 {page_num}: {page_review_count}개 리뷰 수집 (배치 총: {len(batch_reviews)}개)")
                page_num += 1
                
                if len(batch_reviews) >= max_reviews_per_batch:
                    print(f"배치 {batch_num} 완료: {len(batch_reviews)}개 리뷰")
                    break
                    
            except Exception as e:
                print(f"페이지 {page_num} 수집 오류: {e}")
                break
        
        # 배치 리뷰들을 전체 리스트에 추가
        all_product_reviews.extend(batch_reviews)
        
        # 1000개 미만이면 더 이상 리뷰가 없다는 뜻
        if len(batch_reviews) < max_reviews_per_batch:
            print(f"모든 리뷰 수집 완료")
            break
        
        # 다음 배치를 위해 브라우저 새로고침
        print(f"배치 {batch_num} 완료. 다음 배치를 위해 새로고침...")
        driver.refresh()
        time.sleep(5)  # 새로고침 대기
        
        batch_num += 1
    
    print(f"총 {len(all_product_reviews)}개 리뷰 수집 완료 ({batch_num-1}개 배치)")
    return all_product_reviews

def save_product_reviews_csv(reviews, product_name, category_name):
    """제품별 개별 CSV 파일 저장"""
    if not reviews:
        return
    
    # 폴더 생성
    os.makedirs(SAVE_PATH, exist_ok=True)
    
    # 파일명 안전하게 변환
    safe_product_name = re.sub(r'[<>:"/\\|?*]', '_', product_name)[:50]
    filename = f"{category_name}_{safe_product_name}_reviews.csv"
    filepath = os.path.join(SAVE_PATH, filename)
    
    # DataFrame으로 변환 후 저장
    df = pd.DataFrame(reviews)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    
    print(f"저장 완료: {filename} ({len(reviews)}개 리뷰)")

def collect_category_reviews(driver, wait, category_url, category_name, target_products=100):
    """카테고리별 리뷰 수집"""
    driver.get(category_url)
    print(f"\n{category_name} 카테고리 크롤링 시작...")
    
    original_tab = driver.current_window_handle
    
    # 제품들 가져오기
    brand_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.tx_brand")))
    total_products = min(target_products, len(brand_elements))
    print(f"총 {total_products}개 제품 발견")
    
    for product_idx in range(total_products):
        print(f"\n=== {category_name} 제품 {product_idx + 1}/{total_products} ===")
        
        try:
            # 제품 클릭
            current_brands = driver.find_elements(By.CSS_SELECTOR, "span.tx_brand")
            ActionChains(driver).key_down(Keys.CONTROL).click(current_brands[product_idx]).key_up(Keys.CONTROL).perform()
            time.sleep(2)
            
            # 새 탭으로 이동
            all_tabs = driver.window_handles
            new_tab = [tab for tab in all_tabs if tab != original_tab][-1]
            driver.switch_to.window(new_tab)
            time.sleep(3)
            
            # 제품 기본 정보 수집
            try:
                # 페이지 로딩 대기 추가
                product_name_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.prd_name")))
                product_name = product_name_elem.text.strip()
                ranking = product_idx + 1
                
                print(f"제품: {product_name[:50]}...")
                print(f"랭킹: {ranking}")
            except Exception as e:
                print(f"제품명을 찾을 수 없음: {e}")
                print(f"현재 URL: {driver.current_url}")
                driver.close()
                driver.switch_to.window(original_tab)
                continue
            
            # 스크롤 및 리뷰 버튼 클릭
            driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(2)
            
            try:
                review_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "li#reviewInfo a")))
                review_btn.click()
                time.sleep(3)
            except:
                print("리뷰 페이지 접근 실패, 다음 제품으로...")
                driver.close()
                driver.switch_to.window(original_tab)
                continue
            
            # 제품별 리뷰 수집
            product_reviews = collect_product_reviews(driver, product_name, ranking, category_name)
            
            # 제품별 CSV 저장
            if product_reviews:
                save_product_reviews_csv(product_reviews, product_name, category_name)
            
            # 제품 탭 닫고 원본으로 돌아가기
            driver.close()
            driver.switch_to.window(original_tab)
            time.sleep(1)
            
        except Exception as e:
            print(f"제품 {product_idx + 1} 처리 중 오류: {e}")
            try:
                driver.switch_to.window(original_tab)
            except:
                pass
            continue

def main():
    """메인 크롤링 함수"""
    driver = uc.Chrome()
    
    try:
        wait = WebDriverWait(driver, 15)
        
        # 스킨케어 카테고리 수집
        collect_category_reviews(driver, wait, SKINCARE_URL, "skincare", target_products=100)
        
        # 메이크업 카테고리 수집  
        collect_category_reviews(driver, wait, MAKEUP_URL, "makeup", target_products=100)
        
        print(f"\n=== 크롤링 완료 ===")
        print(f"저장 경로: {SAVE_PATH}")
        print("제품별 개별 CSV 파일로 저장 완료")
        
    except Exception as e:
        print(f"크롤링 오류: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()