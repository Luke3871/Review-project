#//==============================================================================//#
"""
쿠팡 리뷰 수집 - 디버깅 & 개선 버전
- 상세한 로깅 추가
- 에러 핸들링 강화
- 구조 확인 기능 추가

last_updated : 2025.09.30
"""
#//==============================================================================//#

import time
import pandas as pd
import os
import glob
from datetime import datetime
from random import randint
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from driver_coupang import make_driver
from navigator_coupang import go_to_page

#//==============================================================================//#
# 디버깅: 페이지 구조 확인
#//==============================================================================//#
def debug_page_structure(driver, product_name):
    """현재 페이지의 리뷰 구조를 분석"""
    from bs4 import BeautifulSoup
    
    print(f"\n{'='*60}")
    print(f"🔍 페이지 구조 디버깅: {product_name[:50]}")
    print(f"{'='*60}")
    
    doc = BeautifulSoup(driver.page_source, "html.parser")
    
    # 1. 리뷰 컨테이너 확인
    review_containers = doc.find_all("article", class_="sdp-review__article__list")
    print(f"✓ 리뷰 컨테이너 ('article.sdp-review__article__list'): {len(review_containers)}개")
    
    if not review_containers:
        print("\n⚠️ 리뷰 컨테이너를 찾을 수 없습니다!")
        print("\n다른 가능한 선택자들을 확인 중...")
        
        # 대안 선택자 확인
        alternatives = [
            ("div.sdp-review__article__list", doc.find_all("div", class_="sdp-review__article__list")),
            ("article[class*='review']", doc.find_all("article", class_=lambda x: x and 'review' in x)),
            ("div[class*='review'][class*='list']", doc.find_all("div", class_=lambda x: x and 'review' in x and 'list' in x)),
        ]
        
        for selector, elements in alternatives:
            if elements:
                print(f"  ✓ 발견: {selector} → {len(elements)}개")
        
        # HTML 일부 저장
        debug_dir = "debug_html"
        os.makedirs(debug_dir, exist_ok=True)
        debug_file = os.path.join(debug_dir, f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"\n💾 전체 HTML 저장: {debug_file}")
        
        return False
    
    # 2. 첫 번째 리뷰의 구조 분석
    print("\n📋 첫 번째 리뷰 구조 분석:")
    first_review = review_containers[0]
    
    # 리뷰어 이름
    reviewer_elem = first_review.find("span", class_="sdp-review__article__list__info__user__name")
    print(f"  • 리뷰어 이름: {'✓' if reviewer_elem else '✗'} {reviewer_elem.text.strip() if reviewer_elem else 'N/A'}")
    
    # 평점
    rating_elem = first_review.find(attrs={"data-rating": True})
    print(f"  • 평점: {'✓' if rating_elem else '✗'} {rating_elem.get('data-rating') if rating_elem else 'N/A'}")
    
    # 날짜
    date_elem = first_review.find(class_='sdp-review__article__list__info__product-info__reg-date')
    print(f"  • 리뷰 날짜: {'✓' if date_elem else '✗'} {date_elem.text.strip() if date_elem else 'N/A'}")
    
    # 리뷰 내용
    content_elem = first_review.find(class_='sdp-review__article__list__review__content')
    print(f"  • 리뷰 내용: {'✓' if content_elem else '✗'} {content_elem.text.strip()[:50] if content_elem else 'N/A'}...")
    
    # 도움이 됨
    help_elem = first_review.find(class_='sdp-review__article__list__help')
    print(f"  • 도움이 됨: {'✓' if help_elem else '✗'} {help_elem.get('data-count') if help_elem else 'N/A'}")
    
    # 구매 옵션
    option_elem = first_review.find("div", class_="sdp-review__article__list__info__product-info__name")
    print(f"  • 구매 옵션: {'✓' if option_elem else '✗'} {option_elem.text.strip() if option_elem else 'N/A'}")
    
    print(f"\n{'='*60}\n")
    return True

#//==============================================================================//#
# 리뷰 수집 함수 (개선 버전)
#//==============================================================================//#
def collect_product_reviews(driver, product_info, max_pages_per_product, collection_date, debug_mode=False):
    """개별 제품의 리뷰 수집 (페이지네이션 포함)"""
    from bs4 import BeautifulSoup
    
    all_reviews = []
    page = 1
    
    # 디버그 모드: 첫 페이지 구조 확인
    if debug_mode and page == 1:
        if not debug_page_structure(driver, product_info['name']):
            return []  # 구조 파악 실패 시 중단
    
    # 제품 상세 페이지에서 추가 정보 추출 (최초 1회만)
    brand_name = ""
    category_use = ""
    
    try:
        doc_initial = BeautifulSoup(driver.page_source, "html.parser")
        
        # 브랜드명 추출
        brand_elem = doc_initial.find("div", class_="twc-text-sm twc-text-blue-600")
        if brand_elem:
            brand_name = brand_elem.text.strip()
        
        # 세부 카테고리 추출 (breadcrumb 마지막 두 항목)
        breadcrumb_items = doc_initial.select("ul.breadcrumb li a")
        if breadcrumb_items:
            if len(breadcrumb_items) >= 2:
                category_use = f"{breadcrumb_items[-2].text.strip()} > {breadcrumb_items[-1].text.strip()}"
            else:
                category_use = breadcrumb_items[-1].text.strip()
            print(f"    [브랜드: {brand_name}] [세부카테고리: {category_use}]")
    except Exception as e:
        print(f"    [제품정보 추출 실패: {e}]")
    
    # 페이지네이션 루프
    consecutive_empty_pages = 0  # 연속 빈 페이지 카운터
    
    while True:
        try:
            print(f"  페이지 {page} 처리 중...", end=" ")
            
            # BeautifulSoup 파싱
            doc = BeautifulSoup(driver.page_source, "html.parser")
            
            # 리뷰 컨테이너 찾기
            review_containers = doc.find_all("article", class_="sdp-review__article__list")
            
            if not review_containers:
                print("리뷰 없음", end=" ")
                consecutive_empty_pages += 1
                
                # 연속 3페이지 리뷰 없으면 종료
                if consecutive_empty_pages >= 3:
                    print("\n  ⚠️ 연속 3페이지 리뷰 없음. 수집 종료")
                    break
                
                # 다음 페이지 시도
                page += 1
                if not go_to_page(driver, page):
                    break
                time.sleep(randint(1, 2))
                continue
            
            # 리뷰 있으면 카운터 리셋
            consecutive_empty_pages = 0
            
            # 모든 help_count를 data-count 속성에서 수집
            all_help_counts = []
            try:
                help_containers = driver.find_elements(By.CSS_SELECTOR, ".sdp-review__article__list__help")
                all_help_counts = [elem.get_attribute("data-count") or "0" for elem in help_containers]
                print(f"(help_count {len(all_help_counts)}개)", end=" ")
            except Exception as e:
                print(f"(help_count오류:{e})", end=" ")
            
            # 평가 항목 수집 (향 만족도, 발색 등) - 있으면
            all_survey_data = []
            try:
                survey_containers = doc.find_all("div", class_="sdp-review__article__list__survey")
                
                if debug_mode and page == 1:
                    print(f"\n  🔍 Survey 컨테이너 발견: {len(survey_containers)}개")
                
                for survey_elem in survey_containers:
                    survey_dict = {}
                    items = survey_elem.find_all("div", class_="sdp-review__article__list__survey__row")
                    
                    for item in items:
                        label_elem = item.find("span", class_="sdp-review__article__list__survey__row__label")
                        value_elem = item.find("span", class_="sdp-review__article__list__survey__row__value")
                        if label_elem and value_elem:
                            label = label_elem.text.strip()
                            value = value_elem.text.strip()
                            survey_dict[label] = value
                            
                            if debug_mode and page == 1 and len(all_survey_data) == 0:
                                print(f"    • {label}: {value}")
                    
                    all_survey_data.append(survey_dict)
                
                if debug_mode and page == 1:
                    print(f"  📊 총 survey_data 수집: {len(all_survey_data)}개")
                    if len(all_survey_data) == 0:
                        print(f"  ⚠️ Survey 데이터 없음 - 이 제품에는 평가 항목이 없을 수 있습니다")
                    
            except Exception as e:
                if debug_mode:
                    print(f"  ❌ Survey 수집 오류: {e}")
            
            page_reviews = 0
            for idx, container in enumerate(review_containers):
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
                    
                    # 도움이 됨 카운트 (순서 매칭)
                    helpful_count = all_help_counts[idx] if idx < len(all_help_counts) else "0"
                    
                    # 선택 옵션 (구매 옵션)
                    selected_option = ""
                    try:
                        option_elem = container.find("div", class_="sdp-review__article__list__info__product-info__name")
                        if option_elem:
                            selected_option = option_elem.text.strip()
                    except:
                        pass
                    
                    # 평가 항목 (향 만족도, 발색 등) - 순서 매칭
                    survey_data = all_survey_data[idx] if idx < len(all_survey_data) else {}
                    
                    if debug_mode and page == 1 and idx == 0:
                        print(f"\n  📋 첫 번째 리뷰의 survey_data: {survey_data}")
                    
                    # review_id 생성
                    review_id = f"coupang_{product_info['rank']:03d}_{page:03d}_{idx+1:03d}"
                    
                    # 리뷰 데이터 구성 (표준 컬럼명 사용 + survey_data 포함)
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
                        'helpful_count': helpful_count,
                        'review_text': review_text
                    }
                    
                    # survey_data 추가 (향 만족도, 발색 등)
                    review_data.update(survey_data)
                    
                    if debug_mode and page == 1 and idx == 0:
                        print(f"  💾 첫 번째 리뷰 전체 데이터 키: {list(review_data.keys())}")
                    
                    all_reviews.append(review_data)
                    page_reviews += 1
                    
                except Exception as e:
                    if debug_mode:
                        print(f"\n  ⚠️ 리뷰 파싱 오류 (idx={idx}): {e}")
                    continue
            
            print(f"✓ {page_reviews}개 리뷰")
            
            # 최대 페이지 제한
            if max_pages_per_product and page >= max_pages_per_product:
                print(f"  ⚠️ 최대 페이지({max_pages_per_product}) 도달")
                break
            
            # 다음 페이지 이동
            next_page = page + 1
            if not go_to_page(driver, next_page):
                print(f"  ⚠️ 페이지 이동 실패 (page={next_page})")
                break
            
            page += 1
            time.sleep(randint(1, 2))
                
        except Exception as e:
            print(f"❌ 오류: {e}")
            if debug_mode:
                import traceback
                traceback.print_exc()
            break
    
    # 제품별 즉시 저장
    if all_reviews:
        reviews_dir = os.path.join("data", "data_coupang", "raw_data", "reviews_coupang")
        os.makedirs(reviews_dir, exist_ok=True)
        
        safe_name = product_info['name'].replace('/', '_').replace('\\', '_')[:50]
        filename = f"{product_info['category']}_{product_info['sort_type']}_rank{product_info['rank']:03d}_{safe_name}.csv"
        filepath = os.path.join(reviews_dir, filename)
        
        reviews_df = pd.DataFrame(all_reviews)
        
        if debug_mode:
            print(f"\n  📊 DataFrame 컬럼: {list(reviews_df.columns)}")
            print(f"  📊 Survey 관련 컬럼: {[col for col in reviews_df.columns if col not in ['review_id', 'captured_at', 'channel', 'product_url', 'product_name', 'brand', 'category', 'category_use', 'product_price_sale', 'product_price_origin', 'sort_type', 'ranking', 'reviewer_name', 'rating', 'review_date', 'selected_option', 'helpful_count', 'review_text']]}")
        
        reviews_df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"  💾 저장: {len(all_reviews)}개 리뷰 → {filename}")
    else:
        print(f"  ⚠️ 수집된 리뷰 없음")
    
    return all_reviews

#//==============================================================================//#
# CSV에서 제품 정보 로드
#//==============================================================================//#
def load_products_from_csv():
    """기존 제품 CSV 파일들을 읽어서 제품 리스트 반환"""
    products_dir = os.path.join("data", "data_coupang", "raw_data", "products_coupang")
    
    if not os.path.exists(products_dir):
        print(f"❌ 제품 디렉토리를 찾을 수 없습니다: {products_dir}")
        return []
    
    csv_files = glob.glob(os.path.join(products_dir, "coupang_*.csv"))
    
    if not csv_files:
        print(f"❌ CSV 파일을 찾을 수 없습니다: {products_dir}")
        return []
    
    print(f"\n✓ 발견된 CSV 파일: {len(csv_files)}개")
    for csv_file in csv_files:
        print(f"  - {os.path.basename(csv_file)}")
    
    # 모든 CSV 파일 읽기
    all_products = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file, encoding='utf-8-sig')
            products = df.to_dict('records')
            all_products.extend(products)
            print(f"  ✓ {os.path.basename(csv_file)}: {len(products)}개 제품")
        except Exception as e:
            print(f"  ❌ {os.path.basename(csv_file)}: 읽기 실패 - {e}")
    
    print(f"\n✓ 총 제품 수: {len(all_products)}개")
    return all_products

#//==============================================================================//#
# 리뷰 수집 메인 함수
#//==============================================================================//#
def crawl_reviews_only(max_pages_per_product=None, start_from=0, debug_mode=False):
    """
    기존 제품 CSV에서 읽어온 제품들의 리뷰만 수집
    
    Args:
        max_pages_per_product: 제품당 최대 페이지 수 (None = 무제한)
        start_from: 몇 번째 제품부터 시작할지 (0부터 시작)
        debug_mode: 디버그 모드 활성화 (True/False)
    """
    print("\n" + "="*60)
    print("🛒 쿠팡 리뷰 수집 시작 (제품 CSV 읽기)")
    print("="*60)
    
    # 수집 시작 시간 기록
    collection_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"⏰ 수집 시작 시간: {collection_date}")
    print(f"🔧 디버그 모드: {'ON' if debug_mode else 'OFF'}")
    
    # CSV에서 제품 정보 로드
    products = load_products_from_csv()
    
    if not products:
        print("❌ 제품 정보를 찾을 수 없습니다.")
        return
    
    # start_from 적용
    if start_from > 0:
        products = products[start_from:]
        print(f"\n▶️ {start_from+1}번째 제품부터 시작 (남은 제품: {len(products)}개)")
    
    driver = make_driver()
    
    try:
        success_count = 0
        fail_count = 0
        total_reviews = 0
        
        for i, product in enumerate(products, start=start_from+1):
            print(f"\n{'='*60}")
            print(f"[{i}/{start_from+len(products)}] {product['name'][:50]}...")
            print(f"{'='*60}")
            
            try:
                driver.get(product['url'])
                print(f"📍 URL: {product['url']}")
                
                # 페이지 로딩 대기 (리뷰 컨테이너가 나타날 때까지)
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "article.sdp-review__article__list"))
                    )
                    print("✓ 페이지 로딩 완료")
                    time.sleep(2)
                except:
                    print("⚠️ 페이지 로딩 타임아웃 (리뷰가 없을 수 있음)")
                    fail_count += 1
                    
                    if debug_mode:
                        debug_page_structure(driver, product['name'])
                    
                    time.sleep(2)
                    continue
                
                reviews = collect_product_reviews(
                    driver, 
                    product, 
                    max_pages_per_product, 
                    collection_date,
                    debug_mode=debug_mode
                )
                
                if reviews:
                    print(f"✅ 완료: {len(reviews)}개 리뷰")
                    success_count += 1
                    total_reviews += len(reviews)
                else:
                    print(f"⚠️ 완료: 리뷰 없음")
                    fail_count += 1
                
                time.sleep(randint(2, 4))
                
            except Exception as e:
                print(f"❌ 오류: {e}")
                fail_count += 1
                if debug_mode:
                    import traceback
                    traceback.print_exc()
                continue
        
        print("\n" + "="*60)
        print("🎉 리뷰 수집 완료!")
        print("="*60)
        print(f"✅ 성공: {success_count}개 제품")
        print(f"❌ 실패: {fail_count}개 제품")
        print(f"📊 총 리뷰: {total_reviews}개")
        print("="*60)
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️ 사용자에 의해 중단됨 (마지막 처리: {i}번째 제품)")
        print(f"💡 다음 실행 시 start_from={i}로 시작하면 이어서 진행 가능")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
        print("\n🔒 브라우저 종료")

#//==============================================================================//#
# 메인 실행
#//==============================================================================//#
if __name__ == "__main__":
    # 옵션 설정
    MAX_PAGES_PER_PRODUCT = None  # None = 모든 페이지, 숫자 = 제한
    START_FROM = 0  # 몇 번째 제품부터 시작할지 (0부터 시작)
    DEBUG_MODE = True  # 첫 제품에서 구조 확인 후 진행
    
    crawl_reviews_only(
        max_pages_per_product=MAX_PAGES_PER_PRODUCT,
        start_from=START_FROM,
        debug_mode=DEBUG_MODE
    )