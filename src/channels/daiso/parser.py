#//==============================================================================//#
"""
다이소 제품 데이터 수집 및 파싱 클래스

기능:
- 스킨케어/메이크업 카테고리별 TOP N 제품 수집
- 악세서리 필터링
- 박스 제품 제외
- 데이터 구조화 및 저장

last_updated : 2025.09.08
"""
#//==============================================================================//#

#//==============================================================================//#
# Library import
#//==============================================================================//#
import time
import pandas as pd
import os
from typing import List, Dict, Tuple, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 다이소 모듈 import
from channels.daiso.config_daiso import (
    CARD_ITEM, 
    CARD_THUMB_LINK, 
    CARD_ITEM_NAME,
    DROPDOWN_BUTTON,
    DROPDOWN_OPTION,
    CATEGORY_URLS,
    EXCLUDE_KEYWORDS,
    SORT_TEXT_MAP
)
from channels.daiso.driver import make_driver, close_driver, DriverConfig
from channels.daiso.navigator import DaisoNavigator
from channels.daiso.scroller import DaisoScroller

#//==============================================================================//#
# DaisoProductCollector Class
#//==============================================================================//#
class DaisoProductCollector:
    """다이소 제품 수집 메인 클래스"""
    
    def __init__(self, driver_config: Optional[DriverConfig] = None, wait_sec: int = 10):
        """
        초기화
        
        Args:
            driver_config: 드라이버 설정 (None시 기본값 사용)
            wait_sec: 대기 시간 설정
        """
        self.driver_config = driver_config or DriverConfig()
        self.wait_sec = wait_sec
        self.driver = None
        self.navigator = None
        self.scroller = None
        
        # 설정값들
        self.category_urls = CATEGORY_URLS
        self.exclude_keywords = EXCLUDE_KEYWORDS
        self.sort_options = SORT_TEXT_MAP
        
        # 수집 결과 저장
        self.beauty_products = []
        self.accessories = []
    
    def __enter__(self):
        """Context manager 시작"""
        self.start_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 종료"""
        self.close_driver()
    
    def start_driver(self):
        """드라이버 시작 및 관련 객체 초기화"""
        self.driver = make_driver(self.driver_config)
        self.navigator = DaisoNavigator(self.driver, self.wait_sec)
        self.scroller = DaisoScroller(self.driver, self.wait_sec)
        print("드라이버 및 관련 객체 초기화 완료")
    
    def close_driver(self):
        """드라이버 종료"""
        if self.driver:
            close_driver(self.driver)
            self.driver = None
            print("드라이버 종료 완료")
    
    def _setup_category_page(self, category_key: str, sort_key: str = "REVIEW") -> bool:
        """
        카테고리 페이지 설정 (이동 + 정렬)
        
        Args:
            category_key: 'skincare' 또는 'makeup'
            sort_key: 정렬 방식 ("SALES", "REVIEW", "LIKE" 등)
            
        Returns:
            bool: 설정 성공 여부
        """
        try:
            # 카테고리 페이지로 이동
            url = self.category_urls[category_key]
            print(f"{category_key} 페이지 이동: {url}")
            self.driver.get(url)
            time.sleep(3)
            
            # 지정된 정렬 설정
            if self._set_sort(sort_key):
                sort_name = self.sort_options.get(sort_key, sort_key)
                print(f"{sort_name} 정렬 설정 완료")
                time.sleep(2)
                return True
            else:
                print("정렬 설정 실패")
                return False
                
        except Exception as e:
            print(f"카테고리 페이지 설정 실패: {e}")
            return False
    
    def _set_sort(self, sort_key: str) -> bool:
        """지정된 정렬로 변경"""
        try:
            # 정렬명 매핑
            target_text = self.sort_options.get(sort_key)
            if not target_text:
                print(f"알 수 없는 정렬 키: {sort_key}")
                return False
            
            # 드롭다운 열기
            dropdown_btn = WebDriverWait(self.driver, self.wait_sec).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, DROPDOWN_BUTTON))
            )
            dropdown_btn.click()
            time.sleep(1)
            
            # 지정된 정렬 선택
            options = self.driver.find_elements(By.CSS_SELECTOR, DROPDOWN_OPTION)
            for option in options:
                if target_text in option.text:
                    option.click()
                    return True
            
            print(f"정렬 옵션을 찾을 수 없음: {target_text}")
            return False
            
        except Exception as e:
            print(f"정렬 설정 오류: {e}")
            return False
    
    def _is_accessory(self, product_name: str) -> bool:
        """악세서리 여부 확인"""
        return any(keyword in product_name for keyword in self.exclude_keywords)
    
    def _is_box_product(self, product_url: str) -> bool:
        """박스 제품 여부 확인 (URL에 'B' 포함)"""
        return "pdNo=B" in product_url
    
    def collect_category_products(self, category_key: str, sort_key: str = "REVIEW", target_count: int = 100) -> Tuple[List[Dict], List[Dict]]:
        """
        특정 카테고리에서 제품 수집
        
        Args:
            category_key: 'skincare' 또는 'makeup'
            sort_key: 정렬 방식 ("SALES", "REVIEW", "LIKE" 등)
            target_count: 목표 수집 개수
            
        Returns:
            Tuple[화장품 리스트, 악세서리 리스트]
        """
        sort_name = self.sort_options.get(sort_key, sort_key)
        print(f"\n=== {category_key.upper()} - {sort_name} 수집 시작 (목표: {target_count}개) ===")
        
        # 카테고리 페이지 설정 (정렬 포함)
        if not self._setup_category_page(category_key, sort_key):
            return [], []
        
        beauty_products = []
        accessories = []
        processed_count = 0
        no_new_products_count = 0
        
        while len(beauty_products) < target_count:
            # 현재 로드된 제품 카드들
            cards = self.driver.find_elements(By.CSS_SELECTOR, CARD_ITEM)
            new_cards = cards[processed_count:]
            
            if not new_cards:
                no_new_products_count += 1
                if no_new_products_count >= 3:
                    print(f"더 이상 새로운 제품을 찾을 수 없습니다. (시도 횟수: {no_new_products_count})")
                    break
                
                print("새로운 제품이 없습니다. 스크롤을 시도합니다...")
                self.scroller.scroll_pagedown_simple(n_times=5, pause=1.0)
                time.sleep(2)
                continue
            
            no_new_products_count = 0
            print(f"새로 처리할 카드 수: {len(new_cards)} (총 {len(cards)}개)")
            
            # 새 카드들 처리
            for card in new_cards:
                try:
                    # 제품명 추출
                    name_elem = card.find_element(By.CSS_SELECTOR, CARD_ITEM_NAME)
                    product_name = name_elem.text.strip()
                    
                    # 링크 추출
                    link_elem = card.find_element(By.CSS_SELECTOR, CARD_THUMB_LINK)
                    product_url = link_elem.get_attribute("href")
                    
                    if not product_name or not product_url:
                        continue
                    
                    # 박스 제품 제외
                    if self._is_box_product(product_url):
                        print(f"[{category_key}][박스제품] {product_name} - 제외")
                        continue
                    
                    # 악세서리 분류
                    if self._is_accessory(product_name):
                        accessories.append({
                            "category": category_key,
                            "sort_type": sort_key,
                            "name": product_name,
                            "url": product_url,
                            "type": "accessory"
                        })
                        print(f"[{category_key}][{sort_key}][악세서리] {product_name}")
                    else:
                        # 화장품 추가
                        if len(beauty_products) < target_count:
                            rank = len(beauty_products) + 1
                            beauty_products.append({
                                "category": category_key,
                                "sort_type": sort_key,
                                "rank": rank,
                                "name": product_name,
                                "url": product_url,
                                "type": "beauty"
                            })
                            print(f"[{category_key}][{sort_key}][{rank:3d}] {product_name}")
                            
                            # 목표 달성시 종료
                            if len(beauty_products) >= target_count:
                                break
                
                except Exception as e:
                    print(f"카드 처리 중 오류: {e}")
                    continue
            
            processed_count = len(cards)
            print(f"[{category_key}][{sort_key}] 현재 수집: 화장품 {len(beauty_products)}/{target_count}, 악세서리 {len(accessories)}")
            
            # 추가 스크롤
            if len(beauty_products) < target_count:
                self.scroller.scroll_pagedown_simple(n_times=3, pause=1.0)
                time.sleep(1.5)
        
        return beauty_products, accessories
    
    def save_results_by_sort(self) -> None:
        """
        수집 결과를 정렬별/카테고리별로 구분해서 저장
        """
        if not self.beauty_products:
            print("저장할 화장품 데이터가 없습니다.")
            return
        
        # 출력 경로 저장
        output_dir = "data_daiso/products_daiso"
        os.makedirs(output_dir, exist_ok=True)

        df_all = pd.DataFrame(self.beauty_products)
        
        # 정렬별/카테고리별로 구분해서 저장
        for sort_key in df_all['sort_type'].unique():
            for category in df_all['category'].unique():
                subset = df_all[(df_all['sort_type'] == sort_key) & (df_all['category'] == category)]
                if len(subset) > 0:
                    filename = f"daiso_{category}_{sort_key}_top{len(subset)}.csv"
                    filepath = os.path.join(output_dir, filename)
                    subset.to_csv(filepath, index=False, encoding='utf-8-sig')
                    print(f"저장 완료: {filepath} ({len(subset)}개)")
        
        # 전체 통합 파일도 저장
        all_filename = "all_products_daiso.csv"
        all_filepath = os.path.join(output_dir, all_filename)
        df_all.to_csv(all_filepath, index=False, encoding='utf-8-sig')
        print(f"통합 파일 저장: {all_filepath} ({len(df_all)}개)")

        # 악세서리도 저장
        if self.accessories:
            df_accessories = pd.DataFrame(self.accessories)
            accessories_filename = "daiso_accessories.csv"
            accessories_filepath = os.path.join(output_dir, accessories_filename)
            df_accessories.to_csv(accessories_filepath, index=False, encoding='utf-8-sig')

        print(f"악세서리 데이터 저장: {accessories_filepath} ({len(df_accessories)}개)")

    def get_summary_by_sort(self) -> Dict:
        """정렬별/카테고리별 수집 결과 요약"""
        if not self.beauty_products:
            return {"message": "수집된 데이터가 없습니다."}
        
        summary = {
            "total_beauty": len(self.beauty_products),
            "total_accessories": len(self.accessories),
            "by_sort_category": {}
        }
        
        df = pd.DataFrame(self.beauty_products)
        for sort_key in df['sort_type'].unique():
            summary["by_sort_category"][sort_key] = {}
            for category in df['category'].unique():
                count = len(df[(df['sort_type'] == sort_key) & (df['category'] == category)])
                summary["by_sort_category"][sort_key][category] = count
        
        return summary