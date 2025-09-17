#//==============================================================================//#
"""
다이소 제품 데이터 수집 및 파싱 클래스

기능:
- 스킨케어/메이크업 카테고리별 TOP 100 제품 메타 데이터 수집 (이름, 가격, url, 썸네일 이미지)
- 악세서리 필터링
- 박스 제품 제외
- 스킨케어/메이크업 카테고리별 TOP 100 제품 리뷰 데이터 수집 
    메타 데이터 + 리뷰어, 리뷰날짜, 리뷰 본문, 도움이되요투표수, 간단평가 (3개), 소비자 리뷰 이미지 
- 데이터 구조화 및 저장

last_updated : 2025.09.14
"""
#//==============================================================================//#

#//==============================================================================//#
# Library import
#//==============================================================================//#
import time
import pandas as pd
import os
import requests
import re
from typing import List, Dict, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# 다이소 모듈 import
from config_daiso import (
    CARD_ITEM,
    CARD_THUMB_LINK, 
    CARD_ITEM_NAME,
    CARD_ITEM_PRICE,
    CARD_ITEM_IMAGE,
    CATEGORY_URLS,
    EXCLUDE_KEYWORDS,
    SORT_TEXT_MAP,
    PRODUCTS_PATH,
    PRODUCTS_IMAGE_PATH,
    REVIEWS_PATH,
    REVIEWS_IMAGE_PATH,
    REVIEW_BUTTON,
    REVIEWER_NAME,
    REVIEW_RATING,
    REVIEW_DATE,
    REVIEW_CONTENT,
    REVIEW_HELPFUL,
    REVIEW_INFO_KEY,
    REVIEW_INFO_VALUE,
    REVIEW_IMAGES,
    NEXT_BUTTON
)
from driver import make_driver, close_driver, DriverConfig
from navigator import DaisoNavigator
from scroller import DaisoScroller

#//==============================================================================//#
# DaisoProductCollector Class
#//==============================================================================//#
class DaisoProductCollector:
    """다이소 제품 수집 메인 클래스"""
    
    # 초기화
    def __init__(self, driver_config: Optional[DriverConfig] = None):
        self.driver_config = driver_config or DriverConfig()
        self.driver = None
        self.navigator = None
        self.scroller = None
        
        # 설정값들
        self.category_urls = CATEGORY_URLS
        self.exclude_keywords = EXCLUDE_KEYWORDS
        self.sort_options = SORT_TEXT_MAP
        
        # 수집 결과 저장
        self.products = []
        self.accessories = []
    
    # 수집 시작
    def __enter__(self):
        self.start_driver()
        return self
    
    # 수집 종료
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_driver()
    
    # 드라이버 시작 및 초기화
    def start_driver(self):
        self.driver = make_driver(self.driver_config)
        self.navigator = DaisoNavigator(self.driver)
        self.scroller = DaisoScroller(self.driver)
        print("드라이버 및 관련 객체 초기화 완료")
    
    # 드라이버 종료
    def close_driver(self):
        if self.driver:
            close_driver(self.driver)
            self.driver = None
            print("드라이버 종료")

    # 이미지 다운로드
    def download_image(self, image_url: str, filename: str) -> bool:
        """
        이미지 다운로드 함수

        Args:
            image_url: 이미지 URL
            filename: 저장할 파일명
            
        Returns:
            bool: 다운로드 성공 여부       
        """
        try:
            os.makedirs(PRODUCTS_IMAGE_PATH, exist_ok= True)

            response = requests.get(image_url, timeout= 10)
            if response.status_code == 200:
                filepath = PRODUCTS_IMAGE_PATH / filename
                with open(filepath, "wb") as f:
                    f.write(response.content)
                return True
            return False
        
        except Exception as e:
            print(f"이미지 다운로드 실패 {e}")
            return False
        
    # url에서 제품 id 추출
    def extract_product_id(self, product_url: str) -> str:
        try:
            if "pdNo=" in product_url:
                return product_url.split("pdNo=")[1].split("&")[0]
            return "unknown"
        except:
            return "unknown"        

    # 악세서리류 필터링
    def is_accessory(self, product_name: str) -> bool:
        return any(keyword in product_name for keyword in EXCLUDE_KEYWORDS)
    
    # 박스제품류 필터링
    def is_box_product(self, product_url: str) -> bool:
        return "pdNo=B" in product_url

    def collect_products(self, category: str, sort_type: str, target_count: int = 100) -> List[Dict]:
        """
        제품 수집 메인 함수
        
        Args:
            category: 'skincare' 또는 'makeup'
            sort_type: 'SALES', 'REVIEW', 'LIKE'
            target_count: 목표 수집 개수
            
        Returns:
            List[Dict]: 수집된 제품 리스트
        """
        print(f"\n=== {category} - {sort_type} 수집 시작 ===")

        # 1. 페이지 이동
        url = CATEGORY_URLS[category]
        self.navigator.goto_category(url)
        
        # 2. 카드 로딩 대기
        if not self.scroller.wait_cards():
            print("초기 카드 로딩 실패")
            return []
        
        # 3. 정렬 설정
        sort_text = SORT_TEXT_MAP[sort_type]
        if not self.navigator.open_sort_dropdown():
            print("드롭다운 열기 실패")
            return []
        
        if not self.navigator.click_sort_option(sort_text):
            print("정렬 옵션 선택 실패")
            return []
        
        time.sleep(2)

        # 4. 제품 수집
        products = []
        processed_count = 0
        no_growth = 0
        
        while len(products) < target_count:
            # 현재 로드된 카드들
            cards = self.driver.find_elements(By.CSS_SELECTOR, CARD_ITEM)
            new_cards = cards[processed_count:]
            
            if not new_cards:
                no_growth += 1
                if no_growth >= 3:
                    print("더 이상 제품을 찾을 수 없습니다")
                    break
                
                # 스크롤해서 더 로드
                self.scroller.scroll_pagedown_simple()
                time.sleep(2)
                continue
            
            no_growth = 0
            print(f"새 카드 수: {len(new_cards)} (총 {len(cards)}개)")

            # 새 카드들 처리
            for card in new_cards:
                if len(products) >= target_count:
                    break
                    
                try:
                    # 제품명
                    name_elem = card.find_element(By.CSS_SELECTOR, CARD_ITEM_NAME)
                    product_name = name_elem.text.strip()
                    
                    # URL
                    link_elem = card.find_element(By.CSS_SELECTOR, CARD_THUMB_LINK)
                    product_url = link_elem.get_attribute("href")
                    
                    # 가격
                    try:
                        price_elem = card.find_element(By.CSS_SELECTOR, CARD_ITEM_PRICE)
                        product_price = price_elem.text.strip()
                    except:
                        product_price = "가격 정보 없음"
                    
                    # 썸네일 이미지 URL
                    try:
                        image_elem = card.find_element(By.CSS_SELECTOR, CARD_ITEM_IMAGE)
                        image_url = image_elem.get_attribute("src")
                    except:
                        image_url = None
                    
                    if not product_name or not product_url:
                        continue
                    
                    # 박스 제품 제외
                    if self.is_box_product(product_url):
                        print(f"[박스제품] {product_name} - 제외")
                        continue
                    
                    # 악세서리 제외
                    if self.is_accessory(product_name):
                        print(f"[악세서리] {product_name} - 제외")
                        continue
                    
                    # 제품 ID 추출
                    product_id = self.extract_product_id(product_url)
                    rank = len(products) + 1
                    
                    # 썸네일 이미지 다운로드
                    thumbnail_filename = None
                    if image_url:
                        thumbnail_filename = f"{category}_{sort_type}_rank{rank:03d}_{product_id}.jpg"
                        if self.download_image(image_url, thumbnail_filename):
                            print(f"썸네일 다운로드 성공: {thumbnail_filename}")
                        else:
                            thumbnail_filename = None
                    
                    # 제품 데이터 생성
                    product = {
                        "category": category,
                        "sort_type": sort_type,
                        "rank": rank,
                        "name": product_name,
                        "price": product_price,
                        "url": product_url,
                        "product_id": product_id,
                        "thumbnail_image": thumbnail_filename
                    }
                    
                    products.append(product)
                    print(f"[{rank:3d}] {product_name} - {product_price}")
                
                except Exception as e:
                    print(f"카드 처리 오류: {e}")
                    continue
            
            processed_count = len(cards)
            
            # 더 필요하면 스크롤
            if len(products) < target_count:
                self.scroller.scroll_pagedown_simple()
                time.sleep(2)
        
        print(f"수집 완료: {len(products)}개")
        return products

    # 제품 메타 데이터를 csv로 저장 data 폴더로
    def save_products_csv(self, products: List[Dict], category: str, sort_type: str) -> None:
        if not products:
            print("저장할 제품 데이터가 없습니다")
            return
        
        # 저장 폴더 생성
        os.makedirs(PRODUCTS_PATH, exist_ok=True)
        
        # CSV 저장
        df = pd.DataFrame(products)
        filename = f"daiso_{category}_{sort_type}_top{len(products)}.csv"
        filepath = PRODUCTS_PATH / filename
        
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"CSV 저장 완료: {filepath}")

    # 수집한 url 
    def collect_product_reviews(self, product_url: str, product_name: str, product_id: str, category: str, sort_type: str, rank: int) -> List[Dict]:
        """
        Args:
            product_url: 제품 페이지 URL
            product_name: 제품명
            product_id: 제품 ID
            category: 카테고리
            sort_type: 정렬 타입
            rank: 순위
            
        Returns:
            List[Dict]: 수집된 리뷰 리스트
        """
        print(f"리뷰 수집 시작: {product_name}")

        # 제품 페이지로 이동
        self.driver.get(product_url)
        time.sleep(2)


        # 리뷰 버튼 클릭
        try:
            review_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, REVIEW_BUTTON)))
            review_button.click()

            time.sleep(3)

        except Exception as e:
            print(f"리뷰 버튼 클릭 실패: {e}")
            return []

        # 가격 정보 수집 (리뷰 페이지에서)
        product_price = "가격 정보 없음"
        try:
            price_elem = self.driver.find_element(By.CSS_SELECTOR, "span.value")
            product_price = price_elem.text.strip()
        except:
            pass
        
        all_reviews = []
        page = 1
        
        while True:
            # 현재 페이지 리뷰 수집
            page_reviews = self.parse_reviews_page(product_name, product_price, product_id, category, sort_type, rank)
            
            if not page_reviews:
                break
            
            all_reviews.extend(page_reviews)
            
            # 다음 페이지로 이동
            try:
                next_button = self.driver.find_element(By.CSS_SELECTOR, NEXT_BUTTON)
                if next_button.get_attribute("disabled") is not None:
                    break
                
                next_button.click()
                page += 1
                time.sleep(2)
                
            except Exception:
                break
        
        return all_reviews
    
    def parse_reviews_page(self, product_name: str, product_price: str, product_id: str, category: str, sort_type: str, rank: int) -> List[Dict]:
        """현재 페이지의 리뷰들 파싱"""
        doc = BeautifulSoup(self.driver.page_source, "html.parser")
        
        # 리뷰 요소들 추출
        reviewer_names = [elem.text.strip() for elem in doc.select(REVIEWER_NAME) if elem.text.strip()]
        review_ratings = [elem.text.strip() for elem in doc.select(REVIEW_RATING) if elem.text.strip()]
        review_dates = [elem.text.strip() for elem in doc.select(REVIEW_DATE) if elem.text.strip()]
        review_contents = [elem.text.strip() for elem in doc.select(REVIEW_CONTENT) if elem.text.strip()]
        helpful_counts = [elem.text.strip() for elem in doc.select(REVIEW_HELPFUL)]
        
        # 최소 개수로 맞춤
        min_length = min(len(reviewer_names), len(review_ratings), len(review_dates), len(review_contents))
        if min_length == 0:
            return []
        
        reviews = []
        for i in range(min_length):
            # 도움이 되요 수
            helpful_count = helpful_counts[i] if i < len(helpful_counts) else "0"
            
            # 간단평가 수집 (보습력, 향 등)
            attributes = self.extract_review_attributes(doc, i)
            
            # 리뷰 이미지 수집
            review_images = self.collect_review_images(product_id, i)
            
            review = {
                'product_name': product_name,
                'product_price': product_price,
                'product_id': product_id,
                'category': category,
                'sort_type': sort_type,
                'rank': rank,
                'reviewer_name': reviewer_names[i],
                'rating': review_ratings[i],
                'review_date': review_dates[i],
                'review_text': review_contents[i],
                'helpful_count': helpful_count,
                'review_images': ','.join(review_images) if review_images else None,
                **attributes
            }
            
            reviews.append(review)
        
        return reviews
    
    def extract_review_attributes(self, doc: BeautifulSoup, review_index: int) -> Dict[str, str]:
        """간단평가 (보습력, 향 등) 추출"""
        attributes = {}
        
        try:
            keys = doc.select(REVIEW_INFO_KEY)
            values = doc.select(REVIEW_INFO_VALUE)
            
            for i, (key_elem, value_elem) in enumerate(zip(keys, values)):
                if key_elem and value_elem:
                    key = key_elem.text.strip()
                    value = value_elem.text.strip()
                    if key and value:
                        attributes[key] = value
        
        except Exception as e:
            print(f"간단평가 추출 오류: {e}")
        
        return attributes
    
    def collect_review_images(self, product_id: str, review_index: int) -> List[str]:
        """리뷰 이미지 수집 및 다운로드"""
        try:
            os.makedirs(REVIEWS_IMAGE_PATH, exist_ok=True)
            
            image_elements = self.driver.find_elements(By.CSS_SELECTOR, REVIEW_IMAGES)
            downloaded_files = []
            
            for img_index, img_elem in enumerate(image_elements[:3]):  # 최대 3개
                try:
                    image_url = img_elem.get_attribute("src")
                    if not image_url:
                        continue
                    
                    filename = f"{product_id}_review{review_index+1:03d}_img{img_index+1}.jpg"
                    
                    response = requests.get(image_url, timeout=10)
                    if response.status_code == 200:
                        filepath = REVIEWS_IMAGE_PATH / filename
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        downloaded_files.append(filename)
                
                except Exception as e:
                    continue
            
            return downloaded_files
        
        except Exception as e:
            return []

    def save_products_csv(self, products: List[Dict], category: str, sort_type: str) -> None:
        if not products:
            print("저장할 제품 데이터가 없습니다")
            return
        
        os.makedirs(PRODUCTS_PATH, exist_ok=True)
        
        df = pd.DataFrame(products)
        filename = f"daiso_{category}_{sort_type}_top{len(products)}.csv"
        filepath = PRODUCTS_PATH / filename
        
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"제품 CSV 저장: {filepath}")
    
    def save_reviews_csv(self, reviews: List[Dict], category: str, sort_type: str, product_name: str) -> None:
        """리뷰 데이터를 CSV로 저장"""
        if not reviews:
            return
        
        os.makedirs(REVIEWS_PATH, exist_ok=True)
        
        df = pd.DataFrame(reviews)
        
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', product_name)[:30]
        filename = f"{category}_{sort_type}_{safe_name}_reviews.csv"
        filepath = REVIEWS_PATH / filename
        
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"리뷰 CSV 저장: {filepath}")

    def save_results_by_sort(self) -> None:
        """수집 결과를 정렬별/카테고리별로 구분해서 저장"""
        if not self.products:
            print("저장할 제품 데이터가 없습니다.")
            return
        
        os.makedirs(PRODUCTS_PATH, exist_ok=True)

        df_all = pd.DataFrame(self.products)
        
        # 정렬별/카테고리별로 구분해서 저장
        for sort_key in df_all['sort_type'].unique():
            for category in df_all['category'].unique():
                subset = df_all[(df_all['sort_type'] == sort_key) & (df_all['category'] == category)]
                if len(subset) > 0:
                    filename = f"daiso_{category}_{sort_key}_top{len(subset)}.csv"
                    filepath = PRODUCTS_PATH / filename
                    subset.to_csv(filepath, index=False, encoding='utf-8-sig')
                    print(f"저장 완료: {filepath} ({len(subset)}개)")
        
        # 전체 통합 파일도 저장
        all_filename = "all_products_daiso.csv"
        all_filepath = PRODUCTS_PATH / all_filename
        df_all.to_csv(all_filepath, index=False, encoding='utf-8-sig')
        print(f"통합 파일 저장: {all_filepath} ({len(df_all)}개)")   
