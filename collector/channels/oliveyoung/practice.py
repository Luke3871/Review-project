import undetected_chromedriver as uc
import time
import pandas as pd
import os
import re
import json
import requests
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

SKINCARE_URL = "https://www.oliveyoung.co.kr/store/main/getBestList.do?dispCatNo=900000100100001&fltDispCatNo=10000010001&pageIdx=1&rowsPerPage=8&t_page=랭킹&t_click=판매랭킹_스킨케어"
MAKEUP_URL = "https://www.oliveyoung.co.kr/store/main/getBestList.do?dispCatNo=900000100100001&fltDispCatNo=10000010002&pageIdx=1&rowsPerPage=8&t_page=랭킹&t_click=판매랭킹_메이크업"

BASE_PATH = "data/data_oliveyoung/raw_data"
REVIEWS_PATH = os.path.join(BASE_PATH, "reviews_oliveyoung")
PRODUCTS_PATH = os.path.join(BASE_PATH, "products_oliveyoung")
REVIEWS_IMAGE_PATH = os.path.join(BASE_PATH, "reviews_image_oliveyoung")
PROGRESS_PATH = os.path.join(BASE_PATH, "progress")

COLLECTION_DATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def save_progress(category_name, product_idx):
    os.makedirs(PROGRESS_PATH, exist_ok=True)
    progress_file = os.path.join(PROGRESS_PATH, f"progress_{category_name}.json")
    
    progress = {
        'category': category_name,
        'last_product_idx': product_idx,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def load_progress(category_name):
    progress_file = os.path.join(PROGRESS_PATH, f"progress_{category_name}.json")
    
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            progress = json.load(f)
        print(f"이전 진행 복구: {category_name} - 제품 {progress['last_product_idx']}부터 시작")
        return progress['last_product_idx']
    
    return 0

def collect_product_images(driver, product_id):
    try:
        os.makedirs(REVIEWS_IMAGE_PATH, exist_ok=True)
        downloaded_files = []
        
        try:
            main_img = driver.find_element(By.CSS_SELECTOR, "img#mainImg")
            main_img_url = main_img.get_attribute("src")
            
            if main_img_url and 'placeholder' not in main_img_url.lower():
                high_res_url = main_img_url.replace('/thumbnails/550/', '/thumbnails/1000/')
                filename = f"{product_id}_product_main.jpg"
                
                response = requests.get(high_res_url, timeout=10)
                if response.status_code == 200:
                    filepath = os.path.join(REVIEWS_IMAGE_PATH, filename)
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    downloaded_files.append(filename)
                else:
                    response = requests.get(main_img_url, timeout=10)
                    if response.status_code == 200:
                        filepath = os.path.join(REVIEWS_IMAGE_PATH, filename)
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        downloaded_files.append(filename)
        except:
            pass
        
        try:
            thumb_links = driver.find_elements(By.CSS_SELECTOR, "ul#prd_thumb_list li a[data-img]")
            
            for img_index, link in enumerate(thumb_links, start=1):
                try:
                    image_url = link.get_attribute("data-img")
                    if not image_url or 'placeholder' in image_url.lower():
                        continue
                    
                    high_res_url = image_url.replace('/thumbnails/550/', '/thumbnails/1000/')
                    filename = f"{product_id}_product_sub{img_index}.jpg"
                    
                    response = requests.get(high_res_url, timeout=10)
                    if response.status_code == 200:
                        filepath = os.path.join(REVIEWS_IMAGE_PATH, filename)
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        downloaded_files.append(filename)
                    else:
                        response = requests.get(image_url, timeout=10)
                        if response.status_code == 200:
                            filepath = os.path.join(REVIEWS_IMAGE_PATH, filename)
                            with open(filepath, 'wb') as f:
                                f.write(response.content)
                            downloaded_files.append(filename)
                except:
                    continue
        except:
            pass
        
        return downloaded_files
    except:
        return []

def collect_review_images(driver, product_id, review_index):
    try:
        os.makedirs(REVIEWS_IMAGE_PATH, exist_ok=True)
        image_elements = driver.find_elements(By.CSS_SELECTOR, "div.review-photo img, ul.review-thumb img")
        downloaded_files = []
        
        for img_index, img_elem in enumerate(image_elements[:3], start=1):
            try:
                image_url = img_elem.get_attribute("src")
                if not image_url or 'placeholder' in image_url.lower():
                    continue
                
                if not image_url or image_url.startswith('data:'):
                    image_url = img_elem.get_attribute("data-src")
                
                if not image_url:
                    continue
                
                filename = f"{product_id}_review{review_index+1:03d}_img{img_index}.jpg"
                
                response = requests.get(image_url, timeout=10)
                if response.status_code == 200:
                    filepath = os.path.join(REVIEWS_IMAGE_PATH, filename)
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    downloaded_files.append(filename)
            except:
                continue
        
        return downloaded_files
    except:
        return []

def collect_evaluation_data(driver):
    evaluation_data = {}
    
    try:
        eval_items = driver.find_elements(By.CSS_SELECTOR, "dl.poll_type1 dt span")
        eval_values = driver.find_elements(By.CSS_SELECTOR, "dl.poll_type1 dd span.txt")
        
        items = [ei.text.strip() for ei in eval_items if ei.text.strip()]
        values = [ev.text.strip() for ev in eval_values if ev.text.strip()]
        
        if items and values:
            evaluation_data = dict(zip(items, values))
        
        if not evaluation_data:
            eval_containers = driver.find_elements(By.CSS_SELECTOR, "div.poll_type1")
            for container in eval_containers:
                try:
                    label = container.find_element(By.CSS_SELECTOR, "dt").text.strip()
                    value = container.find_element(By.CSS_SELECTOR, "dd span").text.strip()
                    if label and value:
                        evaluation_data[label] = value
                except:
                    continue
    except:
        pass
    
    return evaluation_data

def extract_category_use(driver):
    try:
        breadcrumbs = driver.find_elements(By.CSS_SELECTOR, "div.prd_breadcrumb a, ul.category li a")
        if breadcrumbs:
            return breadcrumbs[-1].text.strip()
    except:
        pass
    return None

def collect_product_reviews(driver, product_info, product_images, category_use, max_reviews_per_batch=1000):
    all_product_reviews = []
    batch_num = 1
    
    try:
        product_id = product_info['url'].split('prdNo=')[1].split('&')[0]
    except:
        product_id = f"oliveyoung_{product_info['category']}_{product_info['rank']:03d}"
    
    try:
        product_price_before = driver.find_element(By.CSS_SELECTOR, "span.price-1").text.strip()
    except:
        product_price_before = ""
    
    try:
        product_price_after = driver.find_element(By.CSS_SELECTOR, "span.price-2").text.strip()
    except:
        product_price_after = ""
    
    evaluation_data = collect_evaluation_data(driver)
    
    while True:
        print(f"\n배치 {batch_num} 시작 (최대 {max_reviews_per_batch}개)")
        batch_reviews = []
        page_num = 1
        consecutive_empty_pages = 0
        
        while len(batch_reviews) < max_reviews_per_batch:
            print(f"페이지 {page_num} 수집 중...", end=" ")
            
            if page_num > 1:
                try:
                    page_link = driver.find_element(By.CSS_SELECTOR, f"a[data-page-no='{page_num}']")
                    page_link.click()
                    time.sleep(2)
                except:
                    try:
                        next_btn = driver.find_element(By.CSS_SELECTOR, "a.next")
                        if "disabled" in next_btn.get_attribute("class") or not next_btn.is_enabled():
                            print("마지막 페이지")
                            break
                        next_btn.click()
                        time.sleep(2)
                    except:
                        print("더 이상 페이지 없음")
                        break
            
            try:
                review_containers = driver.find_elements(By.CSS_SELECTOR, "ul.inner_list li")
                
                if not review_containers:
                    print("리뷰 없음", end=" ")
                    consecutive_empty_pages += 1
                    
                    if consecutive_empty_pages >= 3:
                        print("\n연속 3페이지 리뷰 없음. 수집 종료")
                        break
                    
                    page_num += 1
                    continue
                
                consecutive_empty_pages = 0
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
                        
                        review_images = collect_review_images(driver, product_id, page_review_count)
                        
                        review_id = f"oliveyoung_{product_info['category']}_{product_info['rank']:03d}_{page_num:03d}_{page_review_count+1:03d}"
                        
                        review_data = {
                            'review_id': review_id,
                            'captured_at': COLLECTION_DATE,
                            'channel': 'OliveYoung',
                            'product_url': product_info['url'],
                            'product_name': product_info['name'],
                            'brand': product_info.get('brand', ''),
                            'category': product_info['category'],
                            'category_use': category_use,
                            'product_price_origin': product_price_before,
                            'product_price_sale': product_price_after,
                            'sort_type': 'best_ranking',
                            'ranking': product_info['rank'],
                            'reviewer_name': reviewer_name,
                            'reviewer_rank': reviewer_rank,
                            'reviewer_skin_features': reviewer_skin_text,
                            'rating': rating,
                            'review_date': review_date,
                            'selected_option': selected_option,
                            'helpful_count': helpful_count,
                            'review_text': review_content,
                            'review_images': ','.join(review_images) if review_images else None,
                            'product_images': ','.join(product_images) if product_images else None
                        }
                        
                        review_data.update(evaluation_data)
                        batch_reviews.append(review_data)
                        page_review_count += 1
                        
                    except:
                        continue
                
                print(f"{page_review_count}개 (배치 총: {len(batch_reviews)}개)")
                page_num += 1
                
                if len(batch_reviews) >= max_reviews_per_batch:
                    print(f"배치 {batch_num} 완료: {len(batch_reviews)}개 리뷰")
                    break
                
            except Exception as e:
                print(f"페이지 {page_num} 수집 오류: {e}")
                break
        
        all_product_reviews.extend(batch_reviews)
        
        if len(batch_reviews) < max_reviews_per_batch:
            print(f"모든 리뷰 수집 완료")
            break
        
        print(f"배치 {batch_num} 완료. 다음 배치를 위해 새로고침...")
        driver.refresh()
        time.sleep(5)
        batch_num += 1
    
    print(f"총 {len(all_product_reviews)}개 리뷰 수집 완료 ({batch_num}개 배치)")
    return all_product_reviews

def save_product_reviews_csv(reviews, product_info):
    if not reviews:
        print("저장할 리뷰 없음")
        return
    
    os.makedirs(REVIEWS_PATH, exist_ok=True)
    safe_product_name = re.sub(r'[<>:"/\\|?*]', '_', product_info['name'])[:50]
    filename = f"{product_info['category']}_rank{product_info['rank']:03d}_{safe_product_name}.csv"
    filepath = os.path.join(REVIEWS_PATH, filename)
    
    df = pd.DataFrame(reviews)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    print(f"저장: {filename} ({len(reviews)}개 리뷰)")

def save_products_info(products_info, category_name):
    if not products_info:
        return
    
    os.makedirs(PRODUCTS_PATH, exist_ok=True)
    filename = f"oliveyoung_{category_name}_products.csv"
    filepath = os.path.join(PRODUCTS_PATH, filename)
    
    df = pd.DataFrame(products_info)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    print(f"제품 정보 저장: {filename} ({len(products_info)}개)")

def collect_category_reviews(driver, wait, category_url, category_name, target_products=100, start_from=0):
    driver.get(category_url)
    print(f"\n{category_name.upper()} 카테고리 크롤링 시작")
    
    original_tab = driver.current_window_handle
    brand_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.tx_brand")))
    total_products = min(target_products, len(brand_elements))
    print(f"총 {total_products}개 제품 발견")
    
    if start_from > 0:
        print(f"{start_from+1}번째 제품부터 시작")
    
    products_info = []
    success_count = 0
    fail_count = 0
    
    for product_idx in range(start_from, total_products):
        print(f"\n[{product_idx + 1}/{total_products}] {category_name.upper()} 제품")
        
        try:
            current_brands = driver.find_elements(By.CSS_SELECTOR, "span.tx_brand")
            ActionChains(driver).key_down(Keys.CONTROL).click(current_brands[product_idx]).key_up(Keys.CONTROL).perform()
            time.sleep(3)
            
            all_tabs = driver.window_handles
            new_tab = [tab for tab in all_tabs if tab != original_tab][-1]
            driver.switch_to.window(new_tab)
            time.sleep(5)
            
            try:
                WebDriverWait(driver, 20).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
            except:
                pass
            
            try:
                product_name_elem = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "p.prd_name"))
                )
                product_name = product_name_elem.text.strip()
                product_url = driver.current_url
                ranking = product_idx + 1
                
                try:
                    product_id = product_url.split('prdNo=')[1].split('&')[0]
                except:
                    product_id = f"oliveyoung_{category_name}_{ranking:03d}"
                
                try:
                    brand = driver.find_element(By.CSS_SELECTOR, "p.prd_brand a").text.strip()
                except:
                    brand = ""
                
                product_info = {
                    'name': product_name,
                    'url': product_url,
                    'rank': ranking,
                    'category': category_name,
                    'brand': brand
                }
                
                products_info.append(product_info)
                print(f"제품: {product_name[:50]}")
                print(f"랭킹: {ranking}, 브랜드: {brand}")
                
            except Exception as e:
                print(f"제품명을 찾을 수 없음: {e}")
                driver.close()
                driver.switch_to.window(original_tab)
                fail_count += 1
                continue
            
            print("제품 이미지 수집 중...")
            product_images = collect_product_images(driver, product_id)
            
            print("소분류 추출 중...")
            category_use = extract_category_use(driver)
            
            driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(3)
            
            try:
                review_btn = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "li#reviewInfo a"))
                )
                review_btn.click()
                time.sleep(5)
            except:
                print("리뷰 페이지 접근 실패")
                driver.close()
                driver.switch_to.window(original_tab)
                fail_count += 1
                continue
            
            product_reviews = collect_product_reviews(driver, product_info, product_images, category_use)
            
            if product_reviews:
                save_product_reviews_csv(product_reviews, product_info)
                success_count += 1
            else:
                fail_count += 1
            
            save_progress(category_name, product_idx)
            
            driver.close()
            driver.switch_to.window(original_tab)
            time.sleep(2)
            
        except KeyboardInterrupt:
            print(f"\n사용자에 의해 중단됨")
            print(f"다음 실행 시 start_from={product_idx}로 시작하면 이어서 진행 가능")
            driver.close()
            driver.switch_to.window(original_tab)
            break
            
        except Exception as e:
            print(f"제품 {product_idx + 1} 처리 중 오류: {e}")
            fail_count += 1
            try:
                driver.switch_to.window(original_tab)
            except:
                pass
            continue
    
    save_products_info(products_info, category_name)
    
    print(f"\n{category_name.upper()} 카테고리 수집 완료")
    print(f"성공: {success_count}개 제품, 실패: {fail_count}개 제품")

def main(resume=False):
    print("\n올리브영 리뷰 크롤러 시작")
    print(f"시작 시간: {COLLECTION_DATE}")
    print(f"이어하기 모드: {'ON' if resume else 'OFF'}")
    
    driver = uc.Chrome()
    
    try:
        wait = WebDriverWait(driver, 20)
        
        skincare_start = load_progress('skincare') if resume else 0
        collect_category_reviews(driver, wait, SKINCARE_URL, 'skincare', target_products=100, start_from=skincare_start)
        
        makeup_start = load_progress('makeup') if resume else 0
        collect_category_reviews(driver, wait, MAKEUP_URL, 'makeup', target_products=100, start_from=makeup_start)
        
        print("\n전체 크롤링 완료!")
        print(f"리뷰: {REVIEWS_PATH}")
        print(f"제품: {PRODUCTS_PATH}")
        print(f"이미지: {REVIEWS_IMAGE_PATH}")
        
    except Exception as e:
        print(f"\n크롤링 오류: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()
        print("\n브라우저 종료")

if __name__ == "__main__":
    RESUME_MODE = False
    main(resume=RESUME_MODE)