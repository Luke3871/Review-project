#//==============================================================================//#
# driver.py 
#//==============================================================================//#
# 필요 라이브러리 임포트
from bs4 import BeautifulSoup
from urllib import request as req
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import numpy as np
from time import sleep
from random import randint
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dataclasses import dataclass
from typing import Optional
#//==============================================================================//#
# Step 0. 셀레니움
#//==============================================================================//#
#//==============================================================================//#
# driver option set up
# 브라우저 실행 옵션을 설정 객체로 관리
"""
headless 창을 안띄우고 실행
window_size 화면 크기르루 고정
script_timeout 페이지 로딩 최대 대기시간
user_agent 다이소에는 접속하는데 필요한 것이 아직은 없음
language 한국어 우선
snadbox 윈도우 환경에서는 필요하지 않음 향후 확장 고려

"""
#//==============================================================================//#
@dataclass
class DriverConfig:
    headless: bool = True
    window_size: str = "1920,1080"
    page_load_timeout: int = 30          
    script_timeout: int = 30             
    implicit_wait: float = 0.0           
    user_agent: Optional[str] = None     
    accept_language: str = "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    sandboxless: bool = True

#//==============================================================================//#

#//==============================================================================//#
# chrome options
"""
Config를 받아서 실제 크롬 실행에 필요한 옵션 객체를 만듦

"""
#//==============================================================================//#
def _make_chrome_options(cfg: DriverConfig) -> Options:
    opts = Options()

    if cfg.headless:
        opts.add_argument("--headless=new")

    if cfg.sandboxless:
        opts.add_argument("--no-sandbox")

    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument(f"--window-size={cfg.window_size}")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--disable-infobars")
    opts.add_argument(f"--lang={cfg.accept_language}")

    if cfg.user_agent:
        opts.add_argument(f"--user-agent={cfg.user_agent}")

    return opts
#//==============================================================================//#
# make_driver
"""
driver 구동

"""
#//==============================================================================//#



def make_driver(cfg: DriverConfig= DriverConfig()) -> webdriver.Chrome:
    
    # driver config의 설정을 받아 드라이버의 옵션 설정
    options = _make_chrome_options(cfg)
    service= Service(ChromeDriverManager().install())

    # 드라이버 생성
    driver = webdriver.Chrome(service= service, options= options)


    driver.set_page_load_timeout(cfg.page_load_timeout)
    driver.set_script_timeout(cfg.script_timeout)
    driver.implicitly_wait(cfg.implicit_wait)

    return driver


def close_driver(driver: webdriver.Chrome):
    try:
        driver.quit()
    except Exception:
        pass


#//==============================================================================//#
"""
url 진입
페이지내 이동
dropdown box 클릭
sorting option select
상품 페이지 돌입 및 종료


option - daiso
last_updated : 2025.08.30
"""
#//==============================================================================//#

#//==============================================================================//#
# Library import
#//==============================================================================//#
from channels.daiso.config_daiso import CARD_ITEM, DROPDOWN_BUTTON, DROPDOWN_OPTION
import time
from typing import Dict
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as W
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
#//==============================================================================//#
# ranking type
#//==============================================================================//#

# 드랍다운 박스
SORT_TEXT_MAP: Dict[str, str] = {
    "RECOMMEND":   "추천순", 
    "NEW":         "신상품순",
    "SALES":       "판매량순",
    "REVIEW":      "리뷰많은순",
    "LIKE":        "좋아요순",
    "PRICE_HIGH":  "가격높은순",
    "PRICE_LOW":   "가격낮은순"
}

#//==============================================================================//#
# Daiso, navigator
#//==============================================================================//#

def open_sort_dropdown(driver, wait_sec=10) -> bool:
    """드롭다운 버튼 열기"""
    try:
        btn = W(driver, wait_sec).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, DROPDOWN_BUTTON))
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        try:
            btn.click()
        except Exception:
            driver.execute_script("arguments[0].click();", btn)
        return True
    except Exception as e:
        print("[Alert] 드롭다운 버튼 못 찾음:", e)
        return False

def list_sort_options_text(driver, wait_sec=10):
    """드롭다운 옵션 텍스트 리스트"""
    opts = W(driver, wait_sec).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, DROPDOWN_OPTION))
    )
    return [o.text.strip() for o in opts if o.text.strip()]

def _norm(s: str) -> str:
    return (s or "").replace(" ", "").replace("\u200b", "").strip()

def click_sort_option(driver, label_text: str, wait_sec=10):
    """드롭다운이 열린 상태에서 원하는 옵션(label_text)을 클릭"""
    opts = W(driver, wait_sec).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, DROPDOWN_OPTION))
    )
    for o in opts:
        txt = _norm(o.text)
        if txt == _norm(label_text):
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", o)
            try:
                o.click()
            except Exception:
                driver.execute_script("arguments[0].click();", o)
            return True
    return False

def scroll_pagedown(driver, n_times: int = 30, pause: float = 1.0):
    """
    PAGE_DOWN 키를 n_times만큼 눌러서 스크롤 내림
    - driver: Selenium WebDriver
    - n_times: 몇 번 내릴지
    - pause: 각 내림 사이 대기 시간 (초)
    """
    body = driver.find_element(By.TAG_NAME, "body")
    for i in range(n_times):
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(pause)


#//==============================================================================//#
"""
parser

랭킹페이지 내에서 제품 식별자(pdNo)와 제품 URL만 모아서 TOP 100고정
스킨케어 TOP 100
메이크업 TOP 100
고정 될 때 까지 뷰티 악세서리 및 기타 상품의 URL은 따로 수집
이후 크롤링엔 수집한 URL 사용


option - daiso
last_updated : 2025.08.31
"""
#//==============================================================================//#

#//==============================================================================//#
# Library import
#//==============================================================================//#

from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urljoin, urlparse, parse_qs
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from channels.daiso.config_daiso import (
    CARD_ITEM,
    CARD_THUMB_LINK,
    CARD_ITEM_NAME,
    CARD_ITEM_PRICE,
)
from channels.daiso.navigator import DaisoNavigator
import time
#//==============================================================================//#
# Parser preferences
#//==============================================================================//#
# practice.py의 기존 코드 뒤에 추가할 부분
# practice.py 전체 수정본 - 스킨케어/메이크업 카테고리별 수집

# practice.py 전체 수정본 - 스킨케어/메이크업 카테고리별 수집

# 카테고리별 URL
CATEGORY_URLS = {
    "skincare": "https://www.daisomall.co.kr/ds/exhCtgr/C208/CTGR_00014/CTGR_00057",
    "makeup": "https://www.daisomall.co.kr/ds/exhCtgr/C208/CTGR_00014/CTGR_00054"
}

def collect_category_products(driver, category_name, target_count=100):
    """
    특정 카테고리에서 화장품만 필터링하여 TOP N 수집
    """
    exclude_keywords = ["퍼프", "브러시", "펜슬", "스폰지", "도구", "악세서리", "브러쉬", "패드", 
                       "뷰러", "스패츌러", "빗", "집게", "분첩", "면봉", "기름종이"]
    
    beauty_products = []
    accessories = []
    
    print(f"\n=== {category_name.upper()} 카테고리 수집 시작 (목표: {target_count}개) ===")
    
    processed_count = 0  # 이미 처리한 카드 수 추적
    no_new_products_count = 0  # 새 제품이 없는 스크롤 횟수
    
    while len(beauty_products) < target_count:
        # 현재 로드된 모든 제품 카드 가져오기
        cards = driver.find_elements(By.CSS_SELECTOR, "div.goods-unit")
        
        # 새로 추가된 카드들만 처리
        new_cards = cards[processed_count:]
        
        if not new_cards:
            no_new_products_count += 1
            if no_new_products_count >= 3:
                print(f"더 이상 새로운 제품을 찾을 수 없습니다. (시도 횟수: {no_new_products_count})")
                break
                
            print("새로운 제품이 없습니다. 스크롤을 시도합니다...")
            scroll_pagedown(driver, n_times=5, pause=1.0)
            time.sleep(2)
            continue
        
        no_new_products_count = 0  # 새 제품이 있으면 카운트 리셋
        print(f"새로 처리할 카드 수: {len(new_cards)} (총 {len(cards)}개)")
        
        for i, card in enumerate(new_cards):
            try:
                # 제품명 추출
                name_elem = card.find_element(By.CSS_SELECTOR, ".tit")
                product_name = name_elem.text.strip()
                
                # 링크 추출
                link_elem = card.find_element(By.CSS_SELECTOR, "a.goods-link")
                product_url = link_elem.get_attribute("href")
                
                if not product_name or not product_url:
                    continue
                
                # 박스 구성품 제외 (URL에 'B'가 포함된 경우)
                if "pdNo=B" in product_url:
                    print(f"[{category_name}][박스제품] {product_name} - 제외")
                    continue
                
                # 악세서리인지 확인
                is_accessory = any(keyword in product_name for keyword in exclude_keywords)
                
                if is_accessory:
                    accessories.append({
                        "category": category_name,
                        "name": product_name,
                        "url": product_url,
                        "type": "accessory"
                    })
                    print(f"[{category_name}][악세서리] {product_name}")
                else:
                    if len(beauty_products) < target_count:
                        rank = len(beauty_products) + 1
                        beauty_products.append({
                            "category": category_name,
                            "rank": rank,
                            "name": product_name,
                            "url": product_url,
                            "type": "beauty"
                        })
                        print(f"[{category_name}][{rank:3d}] {product_name}")
                        
                        # 목표 달성시 종료
                        if len(beauty_products) >= target_count:
                            break
                
            except Exception as e:
                print(f"카드 처리 중 오류: {e}")
                continue
        
        processed_count = len(cards)  # 처리한 카드 수 업데이트
        
        # 진행 상황 출력
        print(f"[{category_name}] 현재 수집: 화장품 {len(beauty_products)}/{target_count}, 악세서리 {len(accessories)}")
        
        # 스크롤해서 더 로드
        if len(beauty_products) < target_count:
            scroll_pagedown(driver, n_times=3, pause=1.0)
            time.sleep(1.5)
    
    return beauty_products, accessories

def collect_both_categories(driver, target_count=100):
    """
    스킨케어와 메이크업 양쪽 카테고리에서 각각 TOP N 수집
    """
    all_beauty_products = []
    all_accessories = []
    
    for category_key, url in CATEGORY_URLS.items():
        print(f"\n{'='*50}")
        print(f"{category_key.upper()} 카테고리 크롤링 시작")
        print(f"URL: {url}")
        print(f"{'='*50}")
        
        try:
            # 카테고리 페이지로 이동
            driver.get(url)
            time.sleep(3)
            
            # 드롭다운 열기 및 리뷰많은순 선택
            if open_sort_dropdown(driver):
                print("드롭다운 열기 성공")
                if click_sort_option(driver, "리뷰많은순"):
                    print("리뷰많은순 정렬 성공")
                    time.sleep(2)
                else:
                    print("리뷰많은순 정렬 실패")
            else:
                print("드롭다운 열기 실패")
            
            # 해당 카테고리 제품 수집
            beauty_products, accessories = collect_category_products(driver, category_key, target_count)
            
            # 전체 리스트에 추가
            all_beauty_products.extend(beauty_products)
            all_accessories.extend(accessories)
            
            print(f"\n[{category_key.upper()}] 수집 완료:")
            print(f"- 화장품: {len(beauty_products)}개")
            print(f"- 악세서리: {len(accessories)}개")
            
        except Exception as e:
            print(f"{category_key} 카테고리 처리 중 오류: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    return all_beauty_products, all_accessories

def save_results(beauty_products, accessories):
    """결과를 CSV 파일로 저장"""
    import pandas as pd
    
    if beauty_products:
        df_beauty = pd.DataFrame(beauty_products)
        filename_beauty = "daiso_beauty_products.csv"
        df_beauty.to_csv(filename_beauty, index=False, encoding='utf-8-sig')
        print(f"\n화장품 데이터 저장: {filename_beauty}")
        
        # 카테고리별 요약
        for category in ['skincare', 'makeup']:
            cat_products = [p for p in beauty_products if p['category'] == category]
            print(f"- {category}: {len(cat_products)}개")
    
    if accessories:
        df_accessories = pd.DataFrame(accessories)
        filename_acc = "daiso_accessories.csv"
        df_accessories.to_csv(filename_acc, index=False, encoding='utf-8-sig')
        print(f"악세서리 데이터 저장: {filename_acc}")

def main():
    """메인 실행 함수"""
    print("=== 다이소 스킨케어/메이크업 크롤러 시작 ===")
    
    # 드라이버 설정 및 생성
    config = DriverConfig(
        headless=False,  # 테스트용으로 화면 보이게
        window_size="1920,1080"
    )
    
    driver = None
    try:
        print("1. 드라이버 생성 중...")
        driver = make_driver(config)
        print("드라이버 생성 완료")
        
        # 양쪽 카테고리 수집 (각각 TOP100)
        beauty_products, accessories = collect_both_categories(driver, target_count=100)
        
        print(f"\n{'='*50}")
        print("전체 수집 완료")
        print(f"{'='*50}")
        print(f"총 화장품: {len(beauty_products)}개")
        print(f"총 악세서리: {len(accessories)}개")
        
        # 카테고리별 상위 5개씩 출력
        for category in ['skincare', 'makeup']:
            cat_products = [p for p in beauty_products if p['category'] == category]
            print(f"\n=== {category.upper()} TOP 5 ===")
            for product in cat_products[:5]:
                print(f"{product['rank']:2d}. {product['name']}")
        
        # 결과 저장
        save_results(beauty_products, accessories)
        
        # 스크린샷 저장
        driver.save_screenshot("daiso_dual_category_result.png")
        print(f"\n스크린샷 저장: daiso_dual_category_result.png")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            print("드라이버 종료 중...")
            close_driver(driver)
            print("드라이버 종료 완료")

if __name__ == "__main__":
    main()