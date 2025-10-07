#//==============================================================================//#
"""
올리브영 크롤러 - 개선 버전

개선 사항:
1. 디버그 모드 추가
2. 진행상황 저장/복구 기능
3. 표준 컬럼명 사용
4. 상세한 로깅
5. 평가 항목 수집 검증

last_updated : 2025.09.30
"""
#//==============================================================================//#

import undetected_chromedriver as uc
import time
import pandas as pd
import os
import re
import json
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 카테고리 URL
SKINCARE_URL = "https://www.oliveyoung.co.kr/store/main/getBestList.do?dispCatNo=900000100100001&fltDispCatNo=10000010001&pageIdx=1&rowsPerPage=8&t_page=랭킹&t_click=판매랭킹_스킨케어"
MAKEUP_URL = "https://www.oliveyoung.co.kr/store/main/getBestList.do?dispCatNo=900000100100001&fltDispCatNo=10000010002&pageIdx=1&rowsPerPage=8&t_page=랭킹&t_click=판매랭킹_메이크업"

# 저장 경로
BASE_PATH = "data/data_oliveyoung/raw_data"
REVIEWS_PATH = os.path.join(BASE_PATH, "reviews_oliveyoung")
PRODUCTS_PATH = os.path.join(BASE_PATH, "products_oliveyoung")
PROGRESS_PATH = os.path.join(BASE_PATH, "progress")

# 전역 설정
DEBUG_MODE = False
COLLECTION_DATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#//==============================================================================//#
# 진행상황 저장/복구
#//==============================================================================//#
def save_progress(category_name, product_idx):
    """현재 진행 상황 저장"""
    os.makedirs(PROGRESS_PATH, exist_ok=True)
    progress_file = os.path.join(PROGRESS_PATH, f"progress_{category_name}.json")
    
    progress = {
        'category': category_name,
        'last_product_idx': product_idx,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)
    
    if DEBUG_MODE:
        print(f"  💾 진행상황 저장: {category_name} - 제품 {product_idx}")

def load_progress(category_name):
    """이전 진행 상황 불러오기"""
    progress_file = os.path.join(PROGRESS_PATH, f"progress_{category_name}.json")
    
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            progress = json.load(f)
        print(f"  ✅ 이전 진행 복구: {category_name} - 제품 {progress['last_product_idx']}부터 시작")
        return progress['last_product_idx']
    
    return 0

#//==============================================================================//#
# 평가 항목 수집 (디버그 강화)
#//==============================================================================//#
def collect_evaluation_data(driver):
    """제품의 평가 항목들 수집 (향, 발색, 커버력 등)"""
    evaluation_data = {}
    
    try:
        # 방법 1: dl.poll_type1 구조
        eval_items = driver.find_elements(By.CSS_SELECTOR, "dl.poll_type1 dt span")
        eval_values = driver.find_elements(By.CSS_SELECTOR, "dl.poll_type1 dd span.txt")
        
        items = [ei.text.strip() for ei in eval_items if ei.text.strip()]
        values = [ev.text.strip() for ev in eval_values if ev.text.strip()]
        
        if items and values:
            evaluation_data = dict(zip(items, values))
            
            if DEBUG_MODE:
                print(f"    📊 평가 항목 수집 (방법1): {list(evaluation_data.keys())}")
        
        # 방법 2: 대안 선택자 시도
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
            
            if DEBUG_MODE and evaluation_data:
                print(f"    📊 평가 항목 수집 (방법2): {list(evaluation_data.keys())}")
        
        if not evaluation_data and DEBUG_MODE:
            print(f"    ⚠️ 평가 항목 없음 (이 제품엔 평가 항목이 없을 수 있음)")
    
    except Exception as e:
        if DEBUG_MODE:
            print(f"    ❌ 평가 항목 수집 오류: {e}")
    
    return evaluation_data

#//==============================================================================//#
# 리뷰 수집 함수 (개선 버전)
#//==============================================================================//#
def collect_product_reviews(driver, product_info, max_reviews_per_batch=1000):
    """개별 제품의 모든 페이지 리뷰 수집 (배치 처리)"""
    all_product_reviews = []
    batch_num = 1
    
    # 제품 기본 정보 수집 (최초 1회)
    try:
        product_price_before = driver.find_element(By.CSS_SELECTOR, "span.price-1").text.strip()
    except:
        product_price_before = ""
    
    try:
        product_price_after = driver.find_element(By.CSS_SELECTOR, "span.price-2").text.strip()
    except:
        product_price_after = ""
    
    # 평가 항목 수집 (최초 1회)
    evaluation_data = collect_evaluation_data(driver)
    
    if DEBUG_MODE:
        print(f"\n  🔍 제품 정보:")
        print(f"    이름: {product_info['name'][:50]}")
        print(f"    가격: {product_price_before} → {product_price_after}")
        print(f"    평가항목: {list(evaluation_data.keys()) if evaluation_data else '없음'}")
    
    while True:
        print(f"\n  --- 배치 {batch_num} 시작 (최대 {max_reviews_per_batch}개) ---")
        batch_reviews = []
        page_num = 1
        consecutive_empty_pages = 0  # 연속 빈 페이지 카운터
        
        while len(batch_reviews) < max_reviews_per_batch:
            print(f"    페이지 {page_num} 수집 중...", end=" ")
            
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
                            print("마지막 페이지")
                            break
                        next_btn.click()
                        time.sleep(2)
                    except:
                        print("더 이상 페이지 없음")
                        break
            
            # 리뷰 데이터 수집
            try:
                # 개별 리뷰 컨테이너들 찾기
                review_containers = driver.find_elements(By.CSS_SELECTOR, "ul.inner_list li")
                
                if not review_containers:
                    print("리뷰 없음", end=" ")
                    consecutive_empty_pages += 1
                    
                    if consecutive_empty_pages >= 3:
                        print("\n    ⚠️ 연속 3페이지 리뷰 없음. 수집 종료")
                        break
                    
                    page_num += 1
                    continue
                
                # 리뷰 있으면 카운터 리셋
                consecutive_empty_pages = 0
                
                page_review_count = 0
                for container in review_containers:
                    if len(batch_reviews) >= max_reviews_per_batch:
                        break
                    
                    try:
                        # 기본 정보
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
                        
                        # review_id 생성
                        review_id = f"oliveyoung_{product_info['category']}_{product_info['rank']:03d}_{page_num:03d}_{page_review_count+1:03d}"
                        
                        # 표준 컬럼명으로 데이터 구성
                        review_data = {
                            'review_id': review_id,
                            'captured_at': COLLECTION_DATE,
                            'channel': 'OliveYoung',
                            'product_url': product_info['url'],
                            'product_name': product_info['name'],
                            'brand': product_info.get('brand', ''),
                            'category': product_info['category'],
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
                            'review_text': review_content
                        }
                        
                        # 평가 항목 추가 (향, 발색, 커버력 등)
                        review_data.update(evaluation_data)
                        
                        batch_reviews.append(review_data)
                        page_review_count += 1
                        
                    except Exception as e:
                        if DEBUG_MODE:
                            print(f"\n    ⚠️ 리뷰 파싱 오류: {e}")
                        continue
                
                print(f"✓ {page_review_count}개 (배치 총: {len(batch_reviews)}개)")
                page_num += 1
                
                if len(batch_reviews) >= max_reviews_per_batch:
                    print(f"    배치 {batch_num} 완료: {len(batch_reviews)}개 리뷰")
                    break
                
            except Exception as e:
                print(f"❌ 페이지 {page_num} 수집 오류: {e}")
                break
        
        # 배치 리뷰들을 전체 리스트에 추가
        all_product_reviews.extend(batch_reviews)
        
        # 1000개 미만이면 더 이상 리뷰가 없다는 뜻
        if len(batch_reviews) < max_reviews_per_batch:
            print(f"  ✅ 모든 리뷰 수집 완료")
            break
        
        # 다음 배치를 위해 브라우저 새로고침
        print(f"  🔄 배치 {batch_num} 완료. 다음 배치를 위해 새로고침...")
        driver.refresh()
        time.sleep(5)
        
        batch_num += 1
    
    print(f"  📊 총 {len(all_product_reviews)}개 리뷰 수집 완료 ({batch_num}개 배치)")
    return all_product_reviews

#//==============================================================================//#
# CSV 저장 (디버그 강화)
#//==============================================================================//#
def save_product_reviews_csv(reviews, product_info):
    """제품별 개별 CSV 파일 저장"""
    if not reviews:
        print(f"  ⚠️ 저장할 리뷰 없음")
        return
    
    # 폴더 생성
    os.makedirs(REVIEWS_PATH, exist_ok=True)
    
    # 파일명 안전하게 변환
    safe_product_name = re.sub(r'[<>:"/\\|?*]', '_', product_info['name'])[:50]
    filename = f"{product_info['category']}_rank{product_info['rank']:03d}_{safe_product_name}.csv"
    filepath = os.path.join(REVIEWS_PATH, filename)
    
    # DataFrame 생성 전 디버깅
    if DEBUG_MODE:
        print(f"\n  🔍 DataFrame 생성 전 확인:")
        first_review = reviews[0]
        print(f"    첫 리뷰 키: {list(first_review.keys())}")
        
        # 평가 항목 키 확인
        standard_keys = {'review_id', 'captured_at', 'channel', 'product_url', 'product_name', 
                        'brand', 'category', 'product_price_origin', 'product_price_sale', 
                        'sort_type', 'ranking', 'reviewer_name', 'reviewer_rank', 
                        'reviewer_skin_features', 'rating', 'review_date', 'selected_option', 
                        'helpful_count', 'review_text'}
        
        evaluation_keys = [k for k in first_review.keys() if k not in standard_keys]
        if evaluation_keys:
            print(f"    ✅ 평가 항목 키: {evaluation_keys}")
        else:
            print(f"    ⚠️ 평가 항목 없음")
    
    # DataFrame으로 변환
    df = pd.DataFrame(reviews)
    
    if DEBUG_MODE:
        print(f"\n  📊 DataFrame 정보:")
        print(f"    Shape: {df.shape}")
        print(f"    전체 컬럼: {list(df.columns)}")
        
        # 평가 항목 컬럼 확인
        standard_cols = {'review_id', 'captured_at', 'channel', 'product_url', 'product_name', 
                        'brand', 'category', 'product_price_origin', 'product_price_sale', 
                        'sort_type', 'ranking', 'reviewer_name', 'reviewer_rank', 
                        'reviewer_skin_features', 'rating', 'review_date', 'selected_option', 
                        'helpful_count', 'review_text'}
        
        evaluation_cols = [col for col in df.columns if col not in standard_cols]
        if evaluation_cols:
            print(f"    ✅ 평가 항목 컬럼: {evaluation_cols}")
            # 샘플 데이터 출력
            for col in evaluation_cols:
                sample_values = df[col].head(3).tolist()
                print(f"      • {col}: {sample_values}")
        else:
            print(f"    ⚠️ 평가 항목 컬럼 없음")
    
    # CSV 저장
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    print(f"  💾 저장: {filename} ({len(reviews)}개 리뷰, {len(df.columns)}개 컬럼)")
    
    if DEBUG_MODE:
        # 저장된 CSV 재확인
        saved_df = pd.read_csv(filepath, encoding='utf-8-sig')
        print(f"  🔍 저장된 CSV 확인: {saved_df.shape}, 컬럼 {len(saved_df.columns)}개")

#//==============================================================================//#
# 제품 정보 저장
#//==============================================================================//#
def save_products_info(products_info, category_name):
    """수집한 제품 정보를 별도 CSV로 저장"""
    if not products_info:
        return
    
    os.makedirs(PRODUCTS_PATH, exist_ok=True)
    
    filename = f"oliveyoung_{category_name}_products.csv"
    filepath = os.path.join(PRODUCTS_PATH, filename)
    
    df = pd.DataFrame(products_info)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    
    print(f"  💾 제품 정보 저장: {filename} ({len(products_info)}개)")

#//==============================================================================//#
# 카테고리별 수집
#//==============================================================================//#
def collect_category_reviews(driver, wait, category_url, category_name, target_products=100, start_from=0):
    """카테고리별 리뷰 수집"""
    driver.get(category_url)
    print(f"\n{'='*60}")
    print(f"🛍️ {category_name.upper()} 카테고리 크롤링 시작")
    print(f"{'='*60}")
    
    original_tab = driver.current_window_handle
    
    # 제품들 가져오기
    brand_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.tx_brand")))
    total_products = min(target_products, len(brand_elements))
    print(f"✓ 총 {total_products}개 제품 발견")
    
    if start_from > 0:
        print(f"▶️ {start_from+1}번째 제품부터 시작")
    
    products_info = []
    success_count = 0
    fail_count = 0
    
    for product_idx in range(start_from, total_products):
        print(f"\n{'='*60}")
        print(f"[{product_idx + 1}/{total_products}] {category_name.upper()} 제품")
        print(f"{'='*60}")
        
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
                product_name_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.prd_name")))
                product_name = product_name_elem.text.strip()
                product_url = driver.current_url
                ranking = product_idx + 1
                
                # 브랜드 정보
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
                
                print(f"📦 제품: {product_name[:50]}")
                print(f"🏆 랭킹: {ranking}")
                print(f"🏷️ 브랜드: {brand}")
                print(f"🔗 URL: {product_url}")
                
            except Exception as e:
                print(f"❌ 제품명을 찾을 수 없음: {e}")
                print(f"   현재 URL: {driver.current_url}")
                driver.close()
                driver.switch_to.window(original_tab)
                fail_count += 1
                continue
            
            # 스크롤 및 리뷰 버튼 클릭
            driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(2)
            
            try:
                review_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "li#reviewInfo a")))
                review_btn.click()
                time.sleep(3)
            except:
                print("⚠️ 리뷰 페이지 접근 실패")
                driver.close()
                driver.switch_to.window(original_tab)
                fail_count += 1
                continue
            
            # 제품별 리뷰 수집
            product_reviews = collect_product_reviews(driver, product_info)
            
            # 제품별 CSV 저장
            if product_reviews:
                save_product_reviews_csv(product_reviews, product_info)
                success_count += 1
            else:
                fail_count += 1
            
            # 진행상황 저장
            save_progress(category_name, product_idx)
            
            # 제품 탭 닫고 원본으로 돌아가기
            driver.close()
            driver.switch_to.window(original_tab)
            time.sleep(1)
            
        except KeyboardInterrupt:
            print(f"\n\n⚠️ 사용자에 의해 중단됨")
            print(f"💡 다음 실행 시 start_from={product_idx}로 시작하면 이어서 진행 가능")
            driver.close()
            driver.switch_to.window(original_tab)
            break
            
        except Exception as e:
            print(f"❌ 제품 {product_idx + 1} 처리 중 오류: {e}")
            fail_count += 1
            try:
                driver.switch_to.window(original_tab)
            except:
                pass
            continue
    
    # 제품 정보 저장
    save_products_info(products_info, category_name)
    
    print(f"\n{'='*60}")
    print(f"✅ {category_name.upper()} 카테고리 수집 완료")
    print(f"{'='*60}")
    print(f"성공: {success_count}개 제품")
    print(f"실패: {fail_count}개 제품")
    print(f"{'='*60}")

#//==============================================================================//#
# 메인 함수
#//==============================================================================//#
def main(debug_mode=False, resume=False):
    """메인 크롤링 함수"""
    global DEBUG_MODE
    DEBUG_MODE = debug_mode
    
    print("\n" + "="*60)
    print("🛍️ 올리브영 리뷰 크롤러 시작")
    print("="*60)
    print(f"⏰ 시작 시간: {COLLECTION_DATE}")
    print(f"🔧 디버그 모드: {'ON' if DEBUG_MODE else 'OFF'}")
    print(f"🔄 이어하기 모드: {'ON' if resume else 'OFF'}")
    
    driver = uc.Chrome()
    
    try:
        wait = WebDriverWait(driver, 15)
        
        # 스킨케어 카테고리 수집
        skincare_start = load_progress('skincare') if resume else 0
        collect_category_reviews(
            driver, wait, SKINCARE_URL, 'skincare', 
            target_products=100, 
            start_from=skincare_start
        )
        
        # 메이크업 카테고리 수집  
        makeup_start = load_progress('makeup') if resume else 0
        collect_category_reviews(
            driver, wait, MAKEUP_URL, 'makeup', 
            target_products=100,
            start_from=makeup_start
        )
        
        print(f"\n{'='*60}")
        print("🎉 전체 크롤링 완료!")
        print(f"{'='*60}")
        print(f"📂 저장 경로:")
        print(f"  - 리뷰: {REVIEWS_PATH}")
        print(f"  - 제품: {PRODUCTS_PATH}")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\n❌ 크롤링 오류: {e}")
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()
    
    finally:
        driver.quit()
        print("\n🔒 브라우저 종료")

if __name__ == "__main__":
    # 설정
    DEBUG_MODE_ON = False  # 첫 실행은 True로 해서 구조 확인
    RESUME_MODE = False    # 중단됐다가 이어서 할 때 True
    
    main(debug_mode=DEBUG_MODE_ON, resume=RESUME_MODE)