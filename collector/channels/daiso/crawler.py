#//==============================================================================//#
"""
다이소 크롤링 메인 실행 파일

기능:
- 다이소 TOP100 제품 수집 (3개 정렬, 2개 카테고리)
- 수집된 제품의 리뷰 크롤링
- 데이터베이스 저장

last_updated : 2025.09.08
"""
#//==============================================================================//#

#//==============================================================================//#
# Library import
#//==============================================================================//#
import os
import sys
import time
from datetime import datetime
from typing import Dict, List

# 현재 스크립트 경로를 기준으로 src 디렉토리 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "..",  'src')
sys.path.insert(0, src_dir)


# 다이소 모듈 import
from parser import DaisoProductCollector
from driver import DriverConfig

#//==============================================================================//#
# 설정
#//==============================================================================//#
# 수집할 정렬 방식 (판매량순, 리뷰많은순, 좋아요순)
TARGET_SORTS = ["SALES", "REVIEW", "LIKE"]

# 기본 카테고리별 목표 수집 개수
TARGET_COUNT = 100

# 드라이버 설정
DRIVER_CONFIG = DriverConfig(
    headless=True,  # 백그라운드 실행
    window_size="1920,1080",
    page_load_timeout=30
)

#//==============================================================================//#
# 메인 크롤링 함수
#//==============================================================================//#
def crawl_daiso_top_products(target_count=TARGET_COUNT):
    """
    다이소 TOP100 제품 수집 메인 함수
    
    Args:
        target_count: 카테고리별 목표 수집 개수
    """
    start_time = datetime.now()
    print(f"=== 다이소 크롤링 시작 ===")
    print(f"시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"대상 정렬: {TARGET_SORTS}")
    print(f"카테고리별 목표: TOP{target_count}")
    print(f"예상 총 수집량: {len(TARGET_SORTS)} × 2 × {target_count} = {len(TARGET_SORTS) * 2 * target_count}개")
    print("=" * 50)
    
    try:
        # Context manager로 안전한 드라이버 관리
        with DaisoProductCollector(DRIVER_CONFIG) as collector:
            
            all_beauty_products = []
            all_accessories = []
            
            # 각 정렬별로 수집 (메인에서 하드코딩)
            for sort_key in TARGET_SORTS:
                for category_key in ["skincare", "makeup"]:
                    print(f"\n--- {category_key} - {sort_key} 수집 중 ---")
                    beauty_products, accessories = collector.collect_category_products(
                        category_key=category_key, 
                        sort_key=sort_key, 
                        target_count=target_count
                    )
                    all_beauty_products.extend(beauty_products)
                    all_accessories.extend(accessories)
            
            # 결과를 collector에 저장
            collector.beauty_products = all_beauty_products
            collector.accessories = all_accessories
            
            # 결과 저장
            print("\n" + "=" * 50)
            print("수집 완료 - 결과 저장 중...")
            collector.save_results_by_sort()
            
            # 수집 결과 요약 (간단 버전)
            print(f"총 화장품: {len(all_beauty_products)}개")
            print(f"총 악세서리: {len(all_accessories)}개")
            
            return True
            
    except Exception as e:
        print(f"\n크롤링 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

def print_summary(summary: Dict, start_time: datetime):
    """수집 결과 요약 출력"""
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "=" * 50)
    print("수집 완료 요약")
    print("=" * 50)
    print(f"소요 시간: {duration}")
    print(f"총 화장품 수집: {summary['total_beauty']}개")
    print(f"총 악세서리 수집: {summary['total_accessories']}개")
    
    print("\n정렬별/카테고리별 상세:")
    for sort_key, categories in summary['by_sort_category'].items():
        sort_name = {
            "SALES": "판매량순",
            "REVIEW": "리뷰많은순", 
            "LIKE": "좋아요순"
        }.get(sort_key, sort_key)
        
        print(f"\n  {sort_name}:")
        for category, count in categories.items():
            category_name = "스킨케어" if category == "skincare" else "메이크업"
            print(f"    - {category_name}: {count}개")
    
    print(f"\n종료 시간: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

#//==============================================================================//#
# 리뷰 크롤링 
#//==============================================================================//#
def crawl_daiso_reviews():
    """
    수집된 제품 URL로부터 리뷰 데이터 크롤링
    """
    print("\n=== 다이소 리뷰 크롤링 시작 ===")
    
    # CSV 파일들 읽어오기
    import re
    import glob
    import pandas as pd
    from bs4 import BeautifulSoup
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from random import randint
    
    products_dir = "data_daiso/products_daiso"
    csv_files = []
    csv_files.extend(glob.glob(os.path.join(products_dir, "daiso_skincare_SALES_*.csv")))
    csv_files.extend(glob.glob(os.path.join(products_dir, "daiso_accessories.csv")))
    
    if not csv_files:
        print("제품 CSV 파일을 찾을 수 없습니다.")
        return False
    
    print(f"발견된 CSV 파일: {len(csv_files)}개")
    
    # 모든 제품 URL 수집    
    all_products = []
    for csv_file in csv_files:
        if "accessories" in csv_file:  # 악세서리 파일은 제외
            continue
            
        df = pd.read_csv(csv_file)
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
    reviews_dir = "data_daiso/reviews_daiso"
    os.makedirs(reviews_dir, exist_ok=True)
    
    try:
        with DaisoProductCollector(DRIVER_CONFIG) as collector:
            all_reviews = []
            
            for i, product in enumerate(all_products, 1):
                print(f"\n[{i}/{len(all_products)}] {product['name']} 리뷰 수집 중...")
                
                try:
                    # 제품 페이지로 이동
                    collector.driver.get(product['url'])
                    time.sleep(2)
                    
                    # 리뷰 버튼 클릭
                    review_button = WebDriverWait(collector.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(., '리뷰')]"))
                    )
                    review_button.click()
                    time.sleep(2)
                    
                    # 가격 정보 수집 (리뷰 페이지에서)
                    product_price = None
                    try:
                        price_elem = collector.driver.find_element(By.CSS_SELECTOR, "span.value")
                        product_price = price_elem.text.strip()
                    except:
                        product_price = "가격 정보 없음"
                    
                    # 리뷰 데이터 수집
                    reviews = collect_product_reviews(collector.driver, product, product_price)
                    all_reviews.extend(reviews)
                    
                    print(f"수집된 리뷰: {len(reviews)}개, 가격: {product_price}")
                    
                    # 요청 간격 조절 (봇 감지 방지)
                    time.sleep(randint(1, 3))
                    
                except Exception as e:
                    print(f"리뷰 수집 실패: {e}")
                    continue
            
            # 리뷰 데이터 저장
            if all_reviews:
                reviews_df = pd.DataFrame(all_reviews)
                
                # 전체 리뷰 파일
                output_file = os.path.join(reviews_dir, "daiso_all_reviews.csv")
                reviews_df.to_csv(output_file, index=False, encoding='utf-8-sig')
                
                # 카테고리별/정렬별 분리 저장
                for category in reviews_df['category'].unique():
                    for sort_type in reviews_df['sort_type'].unique():
                        subset = reviews_df[
                            (reviews_df['category'] == category) & 
                            (reviews_df['sort_type'] == sort_type)
                        ]
                        if len(subset) > 0:
                            filename = f"daiso_reviews_{category}_{sort_type}.csv"
                            filepath = os.path.join(reviews_dir, filename)
                            subset.to_csv(filepath, index=False, encoding='utf-8-sig')
                            print(f"저장: {filepath} ({len(subset)}개 리뷰)")
                
                print(f"\n전체 리뷰 데이터 저장 완료: {output_file} ({len(all_reviews)}개)")
                return True
            else:
                print("수집된 리뷰가 없습니다.")
                return False
                
    except Exception as e:
        print(f"리뷰 크롤링 중 오류: {e}")
        return False

def collect_product_reviews(driver, product_info, product_price, max_pages=None):
    """
    개별 제품 페이지에서 리뷰 수집 (페이지네이션 포함)
    
    Args:
        driver: Selenium WebDriver
        product_info: 제품 정보 딕셔너리
        product_price: 제품 가격
        max_pages: 최대 수집 페이지 수
        
    Returns:
        List[Dict]: 수집된 리뷰 리스트
    """
    from bs4 import BeautifulSoup
    from selenium.webdriver.common.by import By
    from random import randint
    import pandas as pd
    import re
    all_reviews = []
    page = 1
    
    while True :
        try:
            # 현재 페이지 파싱
            doc = BeautifulSoup(driver.page_source, "html.parser")
            
            # 개별 리뷰 요소들 수집
            reviewer_names = [n.text.strip() if n and n.text.strip() else None 
                            for n in doc.find_all("span", class_="name")]
            review_stars = [s.text.strip() if s and s.text.strip() else None 
                          for s in doc.find_all("span", class_="score")]
            review_dates = [d.text.strip() if d and d.text.strip() else None 
                          for d in doc.find_all(class_='review-date')]
            review_contents = [r.text.strip() if r and r.text.strip() else None 
                             for r in doc.find_all(class_='cont')]
            
            # 리뷰 개수 맞추기 (가장 짧은 리스트 길이 기준)
            min_length = min(len(reviewer_names), len(review_stars), 
                           len(review_dates), len(review_contents))
            
            # 리뷰 데이터 구성
            for i in range(min_length):
                review_data = {
                    'product_url': product_info['url'],
                    'product_name': product_info['name'],
                    'product_price': product_price,
                    'category': product_info['category'],
                    'sort_type': product_info['sort_type'],
                    'rank': product_info['rank'],
                    'reviewer_name': reviewer_names[i],
                    'rating': review_stars[i],
                    'review_date': review_dates[i],
                    'review_text': review_contents[i],
                }
                all_reviews.append(review_data)
            
            print(f"페이지 {page}: {min_length}개 리뷰 수집")
            
            # 다음 페이지로 이동
            try:
                next_button = driver.find_element(By.CLASS_NAME, "btn-next")
                
                # disabled 속성 있으면 종료
                if next_button.get_attribute("disabled") is not None:
                    print("마지막 페이지에 도달했습니다.")
                    break
                
                # 다음 페이지 클릭
                driver.execute_script("arguments[0].click();", next_button)
                page += 1
                time.sleep(randint(1, 3))
                
            except Exception:
                print("다음 페이지 버튼을 찾을 수 없습니다.")
                break
                
        except Exception as e:
            print(f"페이지 {page} 처리 중 오류: {e}")
            break
            # 리뷰 수집 완료 후 즉시 저장

    if all_reviews:
        reviews_dir = "data_daiso/reviews_daiso"
        os.makedirs(reviews_dir, exist_ok=True)
        
        # 제품별 파일명 생성
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', product_info['name'])[:50]
        filename = f"{product_info['category']}_{product_info['sort_type']}_{safe_name}_reviews.csv"
        filepath = os.path.join(reviews_dir, filename)
        
        # CSV 저장
        reviews_df = pd.DataFrame(all_reviews)
        reviews_df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"저장 완료: {filepath} ({len(all_reviews)}개 리뷰)")
    
    return all_reviews

#//==============================================================================//#
# main code
#//==============================================================================//#
def main():

    crawl_daiso_reviews()
    
    print("\n프로그램 종료")

if __name__ == "__main__":
    main()